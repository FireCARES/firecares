import copy
import traceback
from firecares.celery import app
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from firecares.firestation.models import FireDepartment, create_quartile_views, LEVEL_CHOICES_REVERSE_DICT, LEVEL_CHOICES_DICT
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
      'select COALESCE(b.risk_category, ''N/A'') as risk_category, fire_sprd, count(*)
        FROM buildingfires a left join (SELECT
          *
        FROM (
          SELECT state,
            fdid,
            inc_date,
            inc_no,
            exp_no,
            geom,
            b.parcel_id,
            b.wkb_geometry,
            b.risk_category,
            ROW_NUMBER() OVER (PARTITION BY state, fdid, inc_date, inc_no, exp_no, geom ORDER BY st_distance(st_centroid(b.wkb_geometry), a.geom)) AS r
          FROM (select * from incidentaddress where state='%(state)s' and fdid='%(fdid)s') a
             left join parcel_risk_category_local b on a.geom && b.wkb_geometry
             ) x
        WHERE
        x.r = 1) b using (state, inc_date, exp_no, fdid, inc_no)
    where state='%(state)s' and fdid='%(fdid)s' and prop_use in (''419'',''429'',''439'',''449'',''459'',''460'',''462'',''464'',''400'')
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

    for result in results:

        if result.get('risk_category') not in LEVEL_CHOICES_REVERSE_DICT:
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

        record, _ = fd.firedepartmentriskmodels_set.get_or_create(level=LEVEL_CHOICES_REVERSE_DICT.get(result['risk_category']))
        old_score = record.dist_model_score

        try:
            dist = dist_model(floor_extent=False, **counts)
            record.dist_model_score = dist.gibbs_sample()
            print 'updating fdid: {2} - {3} risk level from: {0} to {1}.'.format(old_score, record.dist_model_score, fd.id, LEVEL_CHOICES_DICT[record.level])

        except (NotEnoughRecords, ZeroDivisionError):
            print 'Error updating DIST score: {}.'.format(traceback.format_exc())
            record.dist_model_score = None

        if not dry_run:
            record.save()

    record, _ = fd.firedepartmentriskmodels_set.get_or_create(level=LEVEL_CHOICES_REVERSE_DICT.get('All'))
    old_score = record.dist_model_score
    dist_model = dist_model_for_hazard_level('All')

    try:
        dist = dist_model(floor_extent=False, **all_counts)
        record.dist_model_score = dist.gibbs_sample()
        print 'updating fdid: {2} - {3} risk level from: {0} to {1}.'.format(old_score, record.dist_model_score, fd.id, LEVEL_CHOICES_DICT[record.level])

    except (NotEnoughRecords, ZeroDivisionError):
        print 'Error updating DIST score: {}.'.format(traceback.format_exc())
        record.dist_model_score = None

    if not dry_run:
        record.save()


CIVILIAN_CASUALTIES = """select count(1), extract(year from inc_date) as year, COALESCE(b.risk_category, 'N/A') as risk_category
FROM civiliancasualty a left join (SELECT
  *
FROM (
  SELECT state,
    fdid,
    inc_date,
    inc_no,
    exp_no,
    geom,
    b.parcel_id,
    b.wkb_geometry,
    b.risk_category,
    ROW_NUMBER() OVER (PARTITION BY state, fdid, inc_date, inc_no, exp_no, geom ORDER BY st_distance(st_centroid(b.wkb_geometry), a.geom)) AS r
  FROM (select * from incidentaddress where state=%(state)s and fdid=%(fdid)s) a
     left join parcel_risk_category_local b on a.geom && b.wkb_geometry
     ) x
WHERE x.r = 1) b using (state, inc_date, exp_no, fdid, inc_no) where state=%(state)s and fdid=%(fdid)s and extract(year from inc_date) in %(years)s
GROUP by extract(year from inc_date), COALESCE(b.risk_category, 'N/A')
ORDER BY extract(year from inc_date) DESC"""


STRUCTURE_FIRES = """select count(1), extract(year from alarm) as year, COALESCE(b.risk_category, 'N/A') as risk_category
FROM buildingfires a left join (SELECT
  *
FROM (
  SELECT state,
    fdid,
    inc_date,
    inc_no,
    exp_no,
    geom,
    b.parcel_id,
    b.wkb_geometry,
    b.risk_category,
    ROW_NUMBER() OVER (PARTITION BY state, fdid, inc_date, inc_no, exp_no, geom ORDER BY st_distance(st_centroid(b.wkb_geometry), a.geom)) AS r
  FROM (select * from incidentaddress where state=%(state)s and fdid=%(fdid)s) a
     left join parcel_risk_category_local b on a.geom && b.wkb_geometry
     ) x
WHERE x.r = 1) b using (state, inc_date, exp_no, fdid, inc_no) where state=%(state)s and fdid=%(fdid)s and extract(year from alarm) in %(years)s
GROUP by extract(year from alarm), COALESCE(b.risk_category, 'N/A')
ORDER BY extract(year from alarm) DESC"""


FIREFIGHTER_CASUALTIES = """select count(1), extract(year from inc_date) as year, COALESCE(b.risk_category, 'N/A') as risk_category
FROM ffcasualty a left join (SELECT
  *
FROM (
  SELECT state,
    fdid,
    inc_date,
    inc_no,
    exp_no,
    geom,
    b.parcel_id,
    b.wkb_geometry,
    b.risk_category,
    ROW_NUMBER() OVER (PARTITION BY state, fdid, inc_date, inc_no, exp_no, geom ORDER BY st_distance(st_centroid(b.wkb_geometry), a.geom)) AS r
  FROM (select * from incidentaddress where state=%(state)s and fdid=%(fdid)s) a
     left join parcel_risk_category_local b on a.geom && b.wkb_geometry
     ) x
WHERE x.r = 1) b using (state, inc_date, exp_no, fdid, inc_no) where state=%(state)s and fdid=%(fdid)s and extract(year from inc_date) in %(years)s
GROUP by extract(year from inc_date), COALESCE(b.risk_category, 'N/A')
ORDER BY extract(year from inc_date) DESC"""


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
