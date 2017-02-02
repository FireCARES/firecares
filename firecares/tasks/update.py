import copy
import traceback
from firecares.celery import app
from django.contrib.gis.geos import GEOSGeometry
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from firecares.firestation.models import FireDepartment, create_quartile_views, HazardLevels
from firecares.firestation.models import NFIRSStatistic as nfirs
from fire_risk.models import DIST, DISTMediumHazard, DISTHighHazard, NotEnoughRecords
from fire_risk.models.DIST.providers.ahs import ahs_building_areas
from fire_risk.models.DIST.providers.iaff import response_time_distributions
from fire_risk.utils import LogNormalDraw
from firecares.utils import dictfetchall, lenient_summation


def update_scores():
    for fd in FireDepartment.objects.filter(archived=False):
        update_performance_score.delay(fd.id)


def dist_model_for_hazard_level(hazard_level):
    """
    Returns the appropriate DIST model based on the hazard level.
    """
    hazard_level = hazard_level.lower()

    if hazard_level == 'high':
        return DISTHighHazard

    if hazard_level == 'medium':
        return DISTMediumHazard

    return DIST


@app.task(queue='update')
def update_performance_score(id, dry_run=False):
    """
    Updates department performance scores.
    """

    try:
        cursor = connections['nfirs'].cursor()
        fd = FireDepartment.objects.get(id=id)
    except (ConnectionDoesNotExist, FireDepartment.DoesNotExist):
        return

    RESIDENTIAL_FIRES_BY_FDID_STATE = """
    SELECT *
    FROM crosstab(
      'select COALESCE(y.risk_category, ''N/A'') as risk_category, fire_sprd, count(*)
        FROM buildingfires a left join (
          SELECT state,
            fdid,
            inc_date,
            inc_no,
            exp_no,
            geom,
            x.parcel_id,
            x.risk_category
          FROM (select * from incidentaddress a
             left join parcel_risk_category_local b using (parcel_id)
             ) AS x
        ) AS y using (state, inc_date, exp_no, fdid, inc_no)
    where a.state='%(state)s' and a.fdid='%(fdid)s' and prop_use in (''419'',''429'',''439'',''449'',''459'',''460'',''462'',''464'',''400'')
    group by risk_category, fire_sprd
    order by risk_category, fire_sprd ASC')
    AS ct(risk_category text, "1" bigint, "2" bigint, "3" bigint, "4" bigint, "5" bigint);
    """

    cursor.execute(RESIDENTIAL_FIRES_BY_FDID_STATE, {'fdid': fd.fdid, 'state': fd.state})

    results = dictfetchall(cursor)

    all_counts = dict(object_of_origin=0,
                      room_of_origin=0,
                      floor_of_origin=0,
                      building_of_origin=0,
                      beyond=0)

    risk_mapping = {'Low': 1, 'Medium': 2, 'High': 4, 'N/A': 5}

    for result in results:

        if result.get('risk_category') not in risk_mapping:
            continue

        dist_model = dist_model_for_hazard_level(result.get('risk_category'))

        counts = dict(object_of_origin=result.get('1', 0),
                      room_of_origin=result.get('2', 0),
                      floor_of_origin=result.get('3', 0),
                      building_of_origin=result.get('4', 0),
                      beyond=result.get('5', 0))

        # add current risk category to the all risk category
        for key, value in counts.items():
            all_counts[key] += value

        ahs_building_size = ahs_building_areas(fd.fdid, fd.state)

        if ahs_building_size is not None:
            counts['building_area_draw'] = ahs_building_size

        response_times = response_time_distributions.get('{0}-{1}'.format(fd.fdid, fd.state))

        if response_times:
            counts['arrival_time_draw'] = LogNormalDraw(*response_times, multiplier=60)

        record, _ = fd.firedepartmentriskmodels_set.get_or_create(level=risk_mapping[result['risk_category']])
        old_score = record.dist_model_score

        try:
            dist = dist_model(floor_extent=False, **counts)
            record.dist_model_score = dist.gibbs_sample()
            print 'updating fdid: {2} - {3} risk level from: {0} to {1}.'.format(old_score, record.dist_model_score, fd.id, HazardLevels(record.level).name)

        except (NotEnoughRecords, ZeroDivisionError):
            print 'Error updating DIST score: {}.'.format(traceback.format_exc())
            record.dist_model_score = None

        if not dry_run:
            record.save()

    record, _ = fd.firedepartmentriskmodels_set.get_or_create(level=HazardLevels.All.value)
    old_score = record.dist_model_score
    dist_model = dist_model_for_hazard_level('All')

    try:
        dist = dist_model(floor_extent=False, **all_counts)
        record.dist_model_score = dist.gibbs_sample()
        print 'updating fdid: {2} - {3} risk level from: {0} to {1}.'.format(old_score, record.dist_model_score, fd.id, HazardLevels(record.level).name)

    except (NotEnoughRecords, ZeroDivisionError):
        print 'Error updating DIST score: {}.'.format(traceback.format_exc())
        record.dist_model_score = None

    if not dry_run:
        record.save()


CIVILIAN_CASUALTIES = """SELECT count(1) as count, extract(year from a.inc_date) as year, COALESCE(y.risk_category, 'N/A') as risk_level
FROM civiliancasualty a
LEFT JOIN
    (SELECT state, fdid, inc_date, inc_no, exp_no, x.parcel_id, x.risk_category
        FROM ( SELECT *
            FROM incidentaddress a
            LEFT JOIN parcel_risk_category_local using (parcel_id)
        ) AS x
    ) AS y
USING (state, fdid, inc_date, inc_no, exp_no)
WHERE a.state = %(state)s AND a.fdid = %(fdid)s AND extract(year FROM a.inc_date) IN %(years)s
GROUP BY y.risk_category, extract(year from a.inc_date)
ORDER BY extract(year from a.inc_date) DESC"""


STRUCTURE_FIRES = """SELECT count(1) as count, extract(year from a.alarm) as year, COALESCE(y.risk_category, 'N/A') as risk_level
FROM buildingfires a
LEFT JOIN
    (SELECT state, fdid, inc_date, inc_no, exp_no, x.parcel_id, x.risk_category
        FROM ( SELECT *
            FROM incidentaddress a
            LEFT JOIN parcel_risk_category_local using (parcel_id)
        ) AS x
    ) AS y
USING (state, fdid, inc_date, inc_no, exp_no)
WHERE a.state = %(state)s AND a.fdid = %(fdid)s AND extract(year FROM a.inc_date) IN %(years)s
GROUP BY y.risk_category, extract(year from a.alarm)
ORDER BY extract(year from a.alarm) DESC"""


FIREFIGHTER_CASUALTIES = """SELECT count(1) as count, extract(year from a.inc_date) as year, COALESCE(y.risk_category, 'N/A') as risk_level
FROM ffcasualty a
LEFT JOIN
    (SELECT state, fdid, inc_date, inc_no, exp_no, x.parcel_id, x.risk_category
        FROM ( SELECT *
            FROM incidentaddress a
            LEFT JOIN parcel_risk_category_local using (parcel_id)
        ) AS x
    ) AS y
USING (state, fdid, inc_date, inc_no, exp_no)
WHERE a.state = %(state)s AND a.fdid = %(fdid)s AND extract(year FROM a.inc_date) IN %(years)s
GROUP BY y.risk_category, extract(year from a.inc_date)
ORDER BY extract(year from a.inc_date) DESC"""


@app.task(queue='update')
def update_nfirs_counts(id, year=None):
    """
    Queries the NFIRS database for statistics.
    """

    if not id:
        return

    try:
        fd = FireDepartment.objects.get(id=id)
        cursor = connections['nfirs'].cursor()

    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    mapping = {'Low': 1, 'Medium': 2, 'High': 4, 'N/A': 5}

    years = {}
    if not year:
        # get a list of years populated in the NFIRS database
        years_query = "select distinct(extract(year from inc_date)) as year from buildingfires;"
        cursor.execute(years_query)
        # default years to None
        years = {x: {1: None, 2: None, 4: None, 5: None} for x in [int(n[0]) for n in cursor.fetchall()]}
    else:
        years[year] = {1: None, 2: None, 4: None, 5: None}

    params = dict(fdid=fd.fdid, state=fd.state, years=tuple(years.keys()))

    queries = (
        ('civilian_casualties', CIVILIAN_CASUALTIES, params),
        ('residential_structure_fires', STRUCTURE_FIRES, params),
        ('firefighter_casualties', FIREFIGHTER_CASUALTIES, params)
    )

    for statistic, query, params in queries:
        counts = copy.deepcopy(years)
        cursor.execute(query, params)

        for count, year, level in cursor.fetchall():
            mlevel = mapping[level]
            counts[year][mlevel] = count

        for year, levels in counts.items():
            for level, count in levels.items():
                nfirs.objects.update_or_create(year=year, defaults={'count': count}, fire_department=fd, metric=statistic, level=level)
            total = lenient_summation(*map(lambda x: x[1], levels.items()))
            nfirs.objects.update_or_create(year=year, defaults={'count': total}, fire_department=fd, metric=statistic, level=0)


@app.task(queue='update')
def calculate_department_census_geom(fd_id):
    """
    Calculate and cache the owned census geometry for a specific department
    """

    try:
        fd = FireDepartment.objects.get(id=fd_id)
        cursor = connections['nfirs'].cursor()
    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    UNION_CENSUS_TRACTS_FOR_DEPARTMENT = """SELECT ST_Multi(ST_Union(bg.geom))
    FROM nist.tract_years ty
    INNER JOIN census_block_groups_2010 bg
    ON ty.tr10_fid = ('14000US'::text || "substring"((bg.geoid10)::text, 0, 12))
    WHERE ty.fc_dept_id = %(id)s
    GROUP BY ty.fc_dept_id
    """

    cursor.execute(UNION_CENSUS_TRACTS_FOR_DEPARTMENT, {'id': fd.id})

    geom = cursor.fetchone()

    fd.owned_tracts_geom = GEOSGeometry(geom[0])
    fd.save()


@app.task(queue='update')
def create_quartile_views_task():
    """
    Updates the Quartile Materialized Views.
    """
    return create_quartile_views(None)


@app.task(queue='update')
def update_heatmap_file(state, fd_id, id):
    cursor = connections['nfirs'].cursor()

    sql = """
       \COPY (select alarm, a.inc_type, alarms,ff_death, oth_death, ST_X(geom) as x, st_y(geom) as y
       from buildingfires a
       left join incidentaddress b using (state, inc_date, exp_no, fdid, inc_no)
       where state=%s and fdid=%s)
       to PROGRAM 'aws s3 cp - s3://firecares-pipeline/heatmaps/%s-building-fires.csv --acl=\"public-read\"' DELIMITER ',' CSV HEADER;
    """
    cmd = cursor.mogrify(sql, (state, fd_id, id))
    cursor.execute(cmd)


@app.task(queue='update')
def calculate_structure_counts(fd_id):
    try:
        fd = FireDepartment.objects.get(id=fd_id)
        cursor = connections['nfirs'].cursor()
    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    if not fd.owned_tracts_geom:
        return

    STRUCTURE_COUNTS = """SELECT sum(case when l.risk_category = 'Low' THEN 1 ELSE 0 END) as low,
        sum(CASE WHEN l.risk_category = 'Medium' THEN 1 ELSE 0 END) as medium,
        sum(CASE WHEN l.risk_category = 'High' THEN 1 ELSE 0 END) high,
        sum(CASE WHEN l.risk_category is null THEN 1 ELSE 0 END) as na
    FROM parcel_risk_category_local l
    JOIN (SELECT ST_SetSRID(%(owned_geom)s::geometry, 4326) as owned_geom) x
    ON owned_geom && l.wkb_geometry
    WHERE ST_Intersects(owned_geom, l.wkb_geometry)
    """

    cursor.execute(STRUCTURE_COUNTS, {'owned_geom': fd.owned_tracts_geom.wkb})

    mapping = {1: 'low', 2: 'medium', 4: 'high', 5: 'na'}

    tot = 0
    counts = dictfetchall(cursor)[0]

    for l in HazardLevels.values_sans_all():
        rm, _ = fd.firedepartmentriskmodels_set.get_or_create(level=l)
        count = counts[mapping[l]]
        rm.structure_count = count
        rm.save()
        tot = tot + count

    rm, _ = fd.firedepartmentriskmodels_set.get_or_create(level=HazardLevels.All.value)
    rm.structure_count = tot
    rm.save()
