import copy
import csv
import numpy as np
import traceback
import requests
import json
import time
import boto
import alog
import logging
from boto.s3.key import Key
from StringIO import StringIO
from datetime import datetime
from django.db.utils import IntegrityError
from firecares.utils.arcgis2geojson import arcgis2geojson
from firecares.utils import to_multipolygon
from celery import chain
from firecares.celery import app
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, fromstr
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from scipy.stats import lognorm
from firecares.firestation.models import (
    FireStation, FireDepartment, ParcelDepartmentHazardLevel, EffectiveFireFightingForceLevel, Staffing, refresh_quartile_view, HazardLevels, refresh_national_calculations_view)
from firecares.firestation.models import NFIRSStatistic as nfirs
from fire_risk.models import DIST, DISTMediumHazard, DISTHighHazard, NotEnoughRecords
from fire_risk.models.DIST.providers.ahs import ahs_building_areas
from fire_risk.models.DIST.providers.iaff import response_time_distributions
from fire_risk.utils import LogNormalDraw
from firecares.utils import dictfetchall, lenient_summation

def p(msg):
    alog.info(msg)

ISOCHRONE_BREAKS = ['4', '6', '8']
HTTP_TOO_MANY_REQUESTS = 429

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

    p("updating performance score for {}".format(id))

    try:
        cursor = connections['nfirs'].cursor()
        fd = FireDepartment.objects.get(id=id)
    except (ConnectionDoesNotExist, FireDepartment.DoesNotExist):
        return

    # Hack to get around inline SQL string execution and argument escaping in a tuple
    fds = ["''{}''".format(x) for x in fd.fdids]

    RESIDENTIAL_FIRES_BY_FDID_STATE = """
    SELECT *
    FROM crosstab(
      'select COALESCE(y.risk_category, ''N/A'') as risk_category, fire_sprd, count(*)
        FROM joint_buildingfires a left join (
          SELECT state,
            fdid,
            inc_date,
            inc_no,
            exp_no,
            geom,
            x.parcel_id,
            x.risk_category
          FROM (select * from joint_incidentaddress a
             left join parcel_risk_category_local b using (parcel_id)
             ) AS x
        ) AS y using (state, inc_date, exp_no, fdid, inc_no)
    where a.state='%(state)s' and a.fdid in ({fds}) and prop_use in (''419'',''429'',''439'',''449'',''459'',''460'',''462'',''464'',''400'')
        and fire_sprd is not null and fire_sprd != ''''
    group by risk_category, fire_sprd
    order by risk_category, fire_sprd ASC')
    AS ct(risk_category text, "object_of_origin" bigint, "room_of_origin" bigint, "floor_of_origin" bigint, "building_of_origin" bigint, "beyond" bigint);
    """.format(fds=','.join(fds))

    cursor.execute(RESIDENTIAL_FIRES_BY_FDID_STATE, {'state': fd.state})

    results = dictfetchall(cursor)

    all_counts = dict(object_of_origin=0,
                      room_of_origin=0,
                      floor_of_origin=0,
                      building_of_origin=0,
                      beyond=0)

    risk_mapping = {'Low': 1, 'Medium': 2, 'High': 4, 'N/A': 5}

    ahs_building_size = ahs_building_areas(fd.fdid, fd.state)

    for result in results:

        if result.get('risk_category') not in risk_mapping:
            continue

        dist_model = dist_model_for_hazard_level(result.get('risk_category'))

        # Use floor draws based on the LogNormal of the structure type distribution for med/high risk categories
        # TODO: Detect support for number_of_floors_draw on risk model vs being explicit on hazard levels used :/
        if result.get('risk_category') in ['Medium', 'High']:
            rm, _ = fd.firedepartmentriskmodels_set.get_or_create(level=risk_mapping[result['risk_category']])
            if rm.floor_count_coefficients:
                pass
                # TODO
                # dist_model.number_of_floors_draw = LogNormalDraw(*rm.floor_count_coefficients)

        counts = dict(object_of_origin=result['object_of_origin'] or 0,
                      room_of_origin=result['room_of_origin'] or 0,
                      floor_of_origin=result['floor_of_origin'] or 0,
                      building_of_origin=result['building_of_origin'] or 0,
                      beyond=result['beyond'] or 0)

        # add current risk category to the all risk category
        for key, value in counts.items():
            all_counts[key] += value

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
            record.dist_model_score_fire_count = dist.total_fires
            p('updating fdid: {2} - {3} performance score from: {0} to {1}.'.format(old_score, record.dist_model_score, fd.id, HazardLevels(record.level).name))

        except (NotEnoughRecords, ZeroDivisionError):
            p('Error updating DIST score: {}.'.format(traceback.format_exc()))
            record.dist_model_score = None

        if not dry_run:
            record.save()

    # Clear out scores for missing hazard levels
    if not dry_run:
        missing_categories = set(risk_mapping.keys()) - set(map(lambda x: x.get('risk_category'), results))
        for r in missing_categories:
            p('clearing {0} level from {1} due to missing categories in aggregation'.format(r, fd.id))
            record, _ = fd.firedepartmentriskmodels_set.get_or_create(level=risk_mapping[r])
            record.dist_model_score = None
            record.save()

    record, _ = fd.firedepartmentriskmodels_set.get_or_create(level=HazardLevels.All.value)
    old_score = record.dist_model_score
    dist_model = dist_model_for_hazard_level('All')

    try:
        if ahs_building_size is not None:
            all_counts['building_area_draw'] = ahs_building_size

        response_times = response_time_distributions.get('{0}-{1}'.format(fd.fdid, fd.state))

        if response_times:
            all_counts['arrival_time_draw'] = LogNormalDraw(*response_times, multiplier=60)

        dist = dist_model(floor_extent=False, **all_counts)
        record.dist_model_score = dist.gibbs_sample()
        p('updating fdid: {2} - {3} performance score from: {0} to {1}.'.format(old_score, record.dist_model_score, fd.id, HazardLevels(record.level).name))

    except (NotEnoughRecords, ZeroDivisionError):
        p('Error updating DIST score: {}.'.format(traceback.format_exc()))
        record.dist_model_score = None

    if not dry_run:
        record.save()

    p("...updated performance score for {}".format(id))


DROP_TMP_PARCEL_RISK_TABLE = """
    DROP TABLE IF EXISTS {}
    """

TMP_PARCEL_RISK_TABLE = """
    SELECT a.state, a.fdid, a.inc_date, a.inc_no, a.exp_no, a.geom, a.parcel_id, p.risk_category
    INTO {}
    FROM joint_incidentaddress a
    LEFT JOIN parcel_risk_category_local p
    USING (parcel_id)
    WHERE a.state = %(state)s AND a.fdid in %(fdid)s AND extract(year FROM a.inc_date) IN %(years)s
    """

NFIRS_STATS_QUERY = """
    SELECT count(1) as count, extract(year from a.inc_date) as year, COALESCE(b.risk_category, 'N/A') as risk_level
    FROM {stat_table} a
    LEFT JOIN {parcel_risk_table} b
    USING (state, fdid, inc_date, inc_no, exp_no)
    WHERE a.state = %(state)s AND a.fdid in %(fdid)s AND extract(year FROM a.inc_date) IN %(years)s
    GROUP BY b.risk_category, extract(year from a.inc_date)
    ORDER BY extract(year from a.inc_date) DESC
"""

@app.task(queue='update')
def update_fires_heatmap(id):
    try:
        fd = FireDepartment.objects.get(id=id)
        cursor = connections['nfirs'].cursor()
    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    q = """
    SELECT alarm, a.inc_type, alarms,ff_death, oth_death, ST_X(geom) AS x, st_y(geom) AS y, COALESCE(y.risk_category, 'Unknown') AS risk_category
    FROM buildingfires a
    LEFT JOIN  (
        SELECT state, fdid, inc_date, inc_no, exp_no, x.geom, x.parcel_id, x.risk_category
            FROM (
                SELECT *
                FROM incidentaddress a
                LEFT JOIN parcel_risk_category_local
                using (parcel_id)
            ) AS x
        ) AS y
    USING (state, fdid, inc_date, inc_no, exp_no)
    WHERE a.state = %(state)s and a.fdid in %(fdid)s
    """

    cursor.execute(q, params=dict(state=fd.state, fdid=tuple(fd.fdids)))
    res = cursor.fetchall()
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow('alarm,inc_type,alarms,ff_death,oth_death,x,y,risk_category'.split(','))
    for r in res:
        writer.writerow(r)

    s3 = boto.connect_s3()
    k = Key(s3.get_bucket(settings.HEATMAP_BUCKET))
    k.key = '{}-building-fires.csv'.format(id)
    k.set_contents_from_string(out.getvalue())
    k.set_acl('public-read')


@app.task(queue='update')
def update_ems_heatmap(id):
    try:
        fd = FireDepartment.objects.get(id=id)
        cursor = connections['nfirs'].cursor()
    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    q = """
    SELECT bi.alarm, ST_X(geom) AS x, st_y(geom) AS y, COALESCE(y.risk_category, 'Unknown') AS risk_category
    FROM ems.ems a
    INNER JOIN ems.basicincident bi
    ON a.state = bi.state and a.fdid = bi.fdid and a.inc_no = bi.inc_no and a.exp_no = bi.exp_no and to_date(a.inc_date, 'MMDDYYYY') = bi.inc_date
    LEFT JOIN  (
        SELECT state, fdid, inc_date, inc_no, exp_no, x.geom, x.parcel_id, x.risk_category
            FROM (
                SELECT *
                FROM ems.incidentaddress a
                LEFT JOIN parcel_risk_category_local
                using (parcel_id)
            ) AS x
        ) AS y
    ON a.state = y.state and a.fdid = y.fdid and to_date(a.inc_date, 'MMDDYYYY') = y.inc_date and a.inc_no = y.inc_no and a.exp_no = y.exp_no
    WHERE a.state = %(state)s and a.fdid in %(fdid)s
    """

    cursor.execute(q, params=dict(state=fd.state, fdid=tuple(fd.fdids)))
    res = cursor.fetchall()
    out = StringIO()
    writer = csv.writer(out)
    writer.writerow('alarm,x,y,risk_category'.split(','))
    for r in res:
        writer.writerow(r)

    s3 = boto.connect_s3()
    k = Key(s3.get_bucket(settings.HEATMAP_BUCKET))
    k.key = '{}-ems-incidents.csv'.format(id)
    k.set_contents_from_string(out.getvalue())
    k.set_acl('public-read')


@app.task(queue='update')
def update_department(id):
    p("updating department {}".format(id))
    chain(update_nfirs_counts.si(id),
          update_performance_score.si(id), calculate_department_census_geom.si(id)).delay()


@app.task(queue='update')
def refresh_department_views():
    p("updating department Views")
    chain(refresh_quartile_view_task.si(), refresh_national_calculations_view_task.si()).delay()


@app.task(queue='update')
def update_nfirs_counts(id, year=None, stat=None):
    """
    Queries the NFIRS database for statistics.
    """
    if not id:
        return

    try:
        fd = FireDepartment.objects.get(id=id)

    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    p("updating NFIRS counts for {}: {}".format(fd.id, fd.name))

    mapping = {'Low': 1, 'Medium': 2, 'High': 4, 'N/A': 5}

    years = {}
    if not year:
        # get a list of years populated in the NFIRS database
        years_query = "select distinct(extract(year from inc_date)) as year from joint_buildingfires;"
        with connections['nfirs'].cursor() as cursor:
            cursor.execute(years_query)
            # default years to None
            years = {x: {1: None, 2: None, 4: None, 5: None} for x in [int(n[0]) for n in cursor.fetchall()]}
    else:
        years = {y: {1: None, 2: None, 4: None, 5: None} for y in year}

    params = dict(fdid=tuple(fd.fdids), state=fd.state, years=tuple(years.keys()))

    p('building temp table to optimize queries')

    tmp_table_name = 'tmp_{state}_{fdids}_{years}'.format(
        state=params['state'],
        fdids='_'.join(str(fdid) for fdid in params['fdid']),
        years='_'.join(str(year) for year in params['years'])
        )

    tmp_table_query = TMP_PARCEL_RISK_TABLE.format(tmp_table_name)

    with connections['nfirs'].cursor() as cursor:
        cursor.execute(DROP_TMP_PARCEL_RISK_TABLE.format(tmp_table_name))
        cursor.execute(tmp_table_query, params)
        p('temp table created')

    queries = (
        ('civilian_casualties', NFIRS_STATS_QUERY.format(stat_table='joint_civiliancasualty', parcel_risk_table=tmp_table_name), params),
        ('residential_structure_fires', NFIRS_STATS_QUERY.format(stat_table='joint_buildingfires', parcel_risk_table=tmp_table_name), params),
        ('firefighter_casualties', NFIRS_STATS_QUERY.format(stat_table='joint_ffcasualty', parcel_risk_table=tmp_table_name), params),
        ('fire_calls', NFIRS_STATS_QUERY.format(stat_table='joint_fireincident', parcel_risk_table=tmp_table_name), params),
    )

    if stat:
        queries = filter(lambda x: x[0] == stat, queries)

    for statistic, query, params in queries:
        with connections['nfirs'].cursor() as cursor:
            p('querying NFIRS counts: {}'.format(json.dumps(
                {
                    'department_id': fd.id,
                    'department_name': fd.name,
                    'years': list(years.keys()),
                    'statistic': statistic,
                    'timestamp': str(datetime.now()),
                })
            ))

            counts = copy.deepcopy(years)
            start_time = time.time()
            cursor.execute(query, params)
            end_time = time.time()
            p('query took {:.4f} seconds'.format(end_time - start_time))

            for count, year, level in cursor.fetchall():
                counts[int(year)][mapping[level]] = int(count) if count is not None else count

            p('updating NFIRS counts: {}'.format(json.dumps(
                {
                    'department_id': fd.id,
                    'department_name': fd.name,
                    'years': list(years.keys()),
                    'statistic': statistic,
                    'timestamp': str(datetime.now()),
                })
            ))

            for year, levels in counts.items():
                for level, count in levels.items():
                    nfirs.objects.update_or_create(year=year, defaults={'count': count}, fire_department=fd, metric=statistic, level=level)

                total = lenient_summation(*map(lambda x: x[1], levels.items()))
                nfirs.objects.update_or_create(year=year, defaults={'count': total}, fire_department=fd, metric=statistic, level=0)

    with connections['nfirs'].cursor() as cursor:
        cursor.execute('DROP TABLE {}'.format(tmp_table_name))

    p("updated NFIRS counts for {}: {}".format(id, fd.name))

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

    if geom:
        fd.owned_tracts_geom = GEOSGeometry(geom[0])
        fd.save()
    else:
        p('No census geom - {} ({})'.format(fd.name, fd.id))


@app.task(queue='update', rate_limit='5/h')
def refresh_quartile_view_task(*args, **kwargs):
    """
    Updates the Quartile Materialized Views.
    """

    p("updating quartile view")
    refresh_quartile_view()


@app.task(queue='update', rate_limit='5/h')
def refresh_national_calculations_view_task(*args, **kwargs):
    """
    Updates the National Calculation View.
    """

    p("updating national calculations view")
    refresh_national_calculations_view()


@app.task(queue='update')
def calculate_structure_counts(fd_id):
    try:
        fd = FireDepartment.objects.get(id=fd_id)
        cursor = connections['nfirs'].cursor()
    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    # Skip over existing calculations or missing dept owned tracts
    if not fd.owned_tracts_geom or fd.firedepartmentriskmodels_set.filter(structure_count__isnull=False).count() == 5:
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


@app.task(queue='update')
def calculate_story_distribution(fd_id):
    """
    Using the department in combination with similar departments, calculate the story distribution of structures in
    owned census tracts.  Only medium and high risk structures are included in the calculations.
    """

    MAX_STORIES = 108

    try:
        fd = FireDepartment.objects.get(id=fd_id)
        cursor = connections['nfirs'].cursor()
    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    geoms = list(fd.similar_departments.filter(owned_tracts_geom__isnull=False).values_list('owned_tracts_geom', flat=True))
    geoms.append(fd.owned_tracts_geom)

    FIND_STORY_COUNTS = """SELECT count(1), p.story_nbr
    FROM parcel_stories p
    JOIN "LUSE_swg" lu ON lu."Code" = p.land_use,
    (SELECT g.owned_tracts_geom FROM (VALUES {values}) AS g (owned_tracts_geom)) owned_tracts
    WHERE lu.include_in_floor_dist AND lu.risk_category = %(level)s
    AND ST_Intersects(owned_tracts.owned_tracts_geom, p.wkb_geometry)
    GROUP BY p.story_nbr
    ORDER BY count DESC, p.story_nbr;"""

    values = ','.join(['(ST_SetSRID(\'{}\'::geometry, 4326))'.format(geom.hex) for geom in geoms])
    mapping = {2: 'Medium', 4: 'High'}

    def expand(values, weights):
        ret = []
        for v in zip(values, weights):
            ret = ret + [v[0]] * v[1]
        return ret

    for nlevel, level in mapping.items():
        cursor.execute(FIND_STORY_COUNTS.format(values=values), {'level': level})
        res = cursor.fetchall()

        # Filter out `None` story counts and obnoxious values
        a = filter(lambda x: x[1] is not None and x[1] <= MAX_STORIES, res)
        weights = map(lambda x: x[0], a)
        vals = map(lambda x: x[1], a)

        expanded = expand(vals, weights)
        samples = np.random.choice(expanded, size=1000)
        samp = lognorm.fit(samples)

        # Fit curve to story counts
        rm = fd.firedepartmentriskmodels_set.get(level=nlevel)
        rm.floor_count_coefficients = {'shape': samp[0], 'loc': samp[1], 'scale': samp[2]}
        rm.save()

def get_mapbox_isochrone_geometry(x, y, params):
    keep_trying = True
    delay = 1

    url = '{base_url}/isochrone/v1/mapbox/driving/{x},{y}'.format(
        x=x,
        y=y,
        base_url=settings.MAPBOX_BASE_URL,
    )

    while keep_trying:
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            keep_trying = False
        except Exception as e:
            print('Mapbox API error: {}'.format(e))
            print('Reattempting in {} seconds'.format(delay))
            time.sleep(delay)
            # exponential backoff
            delay *= 2

    if 'features' not in response.json():
        return None

    return json.dumps(response.json()['features'][0]['geometry'])

@app.task(queue='dataanalysis')
def update_station_service_areas():
    for firestation in FireStation.objects.filter(archived=False):
        if not (firestation.service_area_0_4 and firestation.service_area_4_6 and firestation.service_area_6_8):
            update_station_service_area(firestation)
        else:
            p('Fire station {id}: {dept} # {station_number} already has drive times'.format(
                id=firestation.id,
                dept=firestation.department,
                station_number=firestation.station_number,
                )
            )

def update_station_service_area(firestation):
    isochrone_geometries = []

    for minute in ISOCHRONE_BREAKS:
        params = {
            'contours_minutes': minute,
            'polygons': 'true',
            'access_token': settings.MAPBOX_ACCESS_TOKEN
        }

        raw_geometry = get_mapbox_isochrone_geometry(firestation.geom.x, firestation.geom.y, params)

        if not raw_geometry:
            p('Service area not found for {id}: {dept} # {station_number}'.format(
                id=firestation.id,
                dept=firestation.department,
                station_number=firestation.station_number,
                ))
            return

        # prevents bad/self-intersecting geometries
        isochrone_geometries.append(GEOSGeometry(raw_geometry).buffer(0))

    # difference the lesser isochrones from the greater ones
    isochrone_geometries[0]
    isochrone_geometries[1] = isochrone_geometries[1].difference(isochrone_geometries[0])
    isochrone_geometries[2] = isochrone_geometries[2].difference(isochrone_geometries[1]).difference(isochrone_geometries[0])

    firestation.service_area_0_4 = to_multipolygon(isochrone_geometries[0])
    firestation.service_area_4_6 = to_multipolygon(isochrone_geometries[1])
    firestation.service_area_6_8 = to_multipolygon(isochrone_geometries[2])

    firestation.save(update_fields=['service_area_0_4', 'service_area_4_6', 'service_area_6_8'])

    p('Fire station {id}: {dept} # {station_number} drive times updated'.format(
        id=firestation.id,
        dept=firestation.department,
        station_number=firestation.station_number,
        )
    )

@app.task(queue='dataanalysis')
def create_parcel_department_hazard_level_rollup_all():
    """
    Task for updating the servicearea table rolling up parcel hazard categories with departement drive time data
    """
    for fd in FireDepartment.objects.values_list('id', flat=True):
        get_parcel_department_hazard_level_rollup(fd)


@app.task(queue='dataanalysis')
def get_parcel_department_hazard_level_rollup(fd_id):
    """
    Update for one department for the drive time hazard level
    """
    stationlist = FireStation.objects.filter(department_id=fd_id, archived=False)
    dept = FireDepartment.objects.filter(id=fd_id)

    if not dept:
        print('Department {} not found.'.format(fd_id))
        return

    dept = dept[0]

    p("Calculating Drive times for:  " + dept.name)

    # use headquarters if no stations
    station_geometries = [{
        "y": round(firestation.geom.y, 5),
        "x": round(firestation.geom.x, 5),
    } for firestation in stationlist] if stationlist else [{
            'y': round(dept.headquarters_geom.y, 5),
            'x': round(dept.headquarters_geom.x, 5),
        }]

    isochrone_geometries = []

    for minute in ISOCHRONE_BREAKS:
        isochrone_geom = None
        params = {
            'contours_minutes': minute,
            'polygons': 'true',
            'access_token': settings.MAPBOX_ACCESS_TOKEN
        }

        for station_geometry in station_geometries:
            raw_geometry = get_mapbox_isochrone_geometry(station_geometry['x'], station_geometry['y'], params)

            if not raw_geometry:
                p('Service area not found for {id}: {dept} # {station_number}'.format(
                    id=firestation.id,
                    dept=firestation.department,
                    station_number=firestation.station_number,
                ))
                continue

            # prevents bad/self-intersecting geometries
            buffered_geometry = GEOSGeometry(raw_geometry).buffer(0)
            # union all of the equivalent isochrone polygons for each station
            isochrone_geom = isochrone_geom.union(buffered_geometry) if isochrone_geom else buffered_geometry

        isochrone_geometries.append(isochrone_geom)

    # difference out the lesser isochrones from the greater ones
    isochrone_geometries[2] = isochrone_geometries[2].difference(isochrone_geometries[1]).difference(isochrone_geometries[0])
    isochrone_geometries[1] = isochrone_geometries[1].difference(isochrone_geometries[0])

    # conver to MultiPolygon geometries
    isochrone_geometries = [to_multipolygon(geom) for geom in isochrone_geometries]

    update_parcel_department_hazard_level(isochrone_geometries, dept)

def update_parcel_department_hazard_level(isochrone_geometries, department):
    """
    Intersect with Parcel layer and update parcel_department_hazard_level table
    0-4 minutes
    4-6 minutes
    6-8 minutes
    """
    cursor = connections['nfirs'].cursor()

    QUERY_INTERSECT_FOR_PARCEL_DRIVETIME = """SELECT sum(case when l.risk_category = 'Low' THEN 1 ELSE 0 END) as low,
        sum(CASE WHEN l.risk_category = 'Medium' THEN 1 ELSE 0 END) as medium,
        sum(CASE WHEN l.risk_category = 'High' THEN 1 ELSE 0 END) high,
        sum(CASE WHEN l.risk_category is null THEN 1 ELSE 0 END) as unknown
        FROM parcel_risk_category_local l
        JOIN (SELECT ST_SetSRID(ST_GeomFromGeoJSON(%(drive_geom)s), 4326) as drive_geom) x
        ON drive_geom && l.wkb_geometry
        WHERE ST_WITHIN(l.wkb_geometry, drive_geom)
        """

    p('Querying Database for parcels')

    results = []

    for geom in isochrone_geometries:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': geom.geojson})
        results.append(dictfetchall(cursor))

    results0, results4, results6 = results
    drivetimegeom_0_4, drivetimegeom_4_6, drivetimegeom_6_8 = isochrone_geometries

    # Overwrite/Update service area is already registered
    if ParcelDepartmentHazardLevel.objects.filter(department_id=department.id):
        existingrecord = ParcelDepartmentHazardLevel.objects.filter(department_id=department.id)
        addhazardlevelfordepartment = existingrecord[0]
        addhazardlevelfordepartment.parcelcount_low_0_4 = results0[0]['low']
        addhazardlevelfordepartment.parcelcount_low_4_6 = results4[0]['low']
        addhazardlevelfordepartment.parcelcount_low_6_8 = results6[0]['low']
        addhazardlevelfordepartment.parcelcount_medium_0_4 = results0[0]['medium']
        addhazardlevelfordepartment.parcelcount_medium_4_6 = results4[0]['medium']
        addhazardlevelfordepartment.parcelcount_medium_6_8 = results6[0]['medium']
        addhazardlevelfordepartment.parcelcount_high_0_4 = results0[0]['high']
        addhazardlevelfordepartment.parcelcount_high_4_6 = results4[0]['high']
        addhazardlevelfordepartment.parcelcount_high_6_8 = results6[0]['high']
        addhazardlevelfordepartment.parcelcount_unknown_0_4 = results0[0]['unknown']
        addhazardlevelfordepartment.parcelcount_unknown_4_6 = results4[0]['unknown']
        addhazardlevelfordepartment.parcelcount_unknown_6_8 = results6[0]['unknown']

        addhazardlevelfordepartment.drivetimegeom_0_4 = drivetimegeom_0_4
        addhazardlevelfordepartment.drivetimegeom_4_6 = drivetimegeom_4_6
        addhazardlevelfordepartment.drivetimegeom_6_8 = drivetimegeom_6_8

        p(department.name + " Service Area Updated")
    else:
        deptservicearea = {}
        deptservicearea['department'] = department
        deptservicearea['parcelcount_low_0_4'] = results0[0]['low']
        deptservicearea['parcelcount_low_4_6'] = results4[0]['low']
        deptservicearea['parcelcount_low_6_8'] = results6[0]['low']
        deptservicearea['parcelcount_medium_0_4'] = results0[0]['medium']
        deptservicearea['parcelcount_medium_4_6'] = results4[0]['medium']
        deptservicearea['parcelcount_medium_6_8'] = results6[0]['medium']
        deptservicearea['parcelcount_high_0_4'] = results0[0]['high']
        deptservicearea['parcelcount_high_4_6'] = results4[0]['high']
        deptservicearea['parcelcount_high_6_8'] = results6[0]['high']
        deptservicearea['parcelcount_unknown_0_4'] = results0[0]['unknown']
        deptservicearea['parcelcount_unknown_4_6'] = results4[0]['unknown']
        deptservicearea['parcelcount_unknown_6_8'] = results6[0]['unknown']

        deptservicearea['drivetimegeom_0_4'] = drivetimegeom_0_4
        deptservicearea['drivetimegeom_4_6'] = drivetimegeom_4_6
        deptservicearea['drivetimegeom_6_8'] = drivetimegeom_6_8

        addhazardlevelfordepartment = ParcelDepartmentHazardLevel.objects.create(**deptservicearea)
        p(department.name + " Service Area Created")

    addhazardlevelfordepartment.save()


@app.task(queue='dataanalysis')
def create_effective_firefighting_rollup_all():
    """
    Task for updating the effective fire fighting force EffectiveFireFightingForceLevel table
    """
    for fd in FireDepartment.objects.values_list('id', flat=True):
        update_parcel_department_effectivefirefighting_rollup(fd)


def get_async_efff_service_status(jobid, dept_name):
    """
    Check status for Drive Time Asynchronous Webservice until there is a results value then call the results url to get json geom
    results: {
        PeopleCount: {
        paramUrl: "results/PeopleCount
    """
    getdrivetimejobstatus = requests.get("http://gis.iaff.org/arcgis/rest/services/Production/PeopleCount2017_V2/GPServer/PeopleCount2017/jobs/" + jobid + "?f=json")

    if 'results' in json.loads(getdrivetimejobstatus.content):
        p("Drive Time Analysis finished for " + dept_name.name)
        drivetimejobfinished = requests.get("http://gis.iaff.org/arcgis/rest/services/Production/PeopleCount2017_V2/GPServer/PeopleCount2017/jobs/" + jobid + "/results/PeopleCount?f=pjson")
        update_parcel_effectivefirefighting_table(json.loads(drivetimejobfinished.content)['value']['features'], dept_name)

    elif json.loads(getdrivetimejobstatus.content)['jobStatus'] == 'esriJobFailed':
        p("Drive Time Analysis errored for " + dept_name.name)

    else:
        p("Drive Time Analysis processing for " + dept_name.name)
        time.sleep(20)
        get_async_efff_service_status(jobid, dept_name)


@app.task(queue='dataanalysis')
def update_parcel_department_effectivefirefighting_rollup(fd_id):
    """
    Update for one department for the effective fire fighting force
    """
    stationlist = FireStation.objects.filter(department_id=fd_id)
    dept = FireDepartment.objects.filter(id=fd_id)
    staffingtotal = "1"  # assume staffing minimum of 1 for now

    if dept[0].owned_tracts_geom is None:

        p("No geometry for the department " + dept[0].name)

    else:
        print "Calculating Response times and staffing for:  " + dept[0].name + ' at ' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        try:
            #  Use Headquarters geometry if there is no Statffing assets
            if len(stationlist) < 1:
                drivetimeurl = 'http://gis.iaff.org/arcgis/rest/services/Production/PeopleCountOct2012/GPServer/PeopleCountOct2012/execute?f=json&Facilities={"features":[{"geometry":{"x":' + str(dept[0].headquarters_geom.x) + ',"spatialReference":{"wkid":4326},"y":' + str(dept[0].headquarters_geom.y) + '}}],"geometryType":"esriGeometryPoint"}&env:outSR=4326&text_input=' + staffingtotal + '&returnZ=false&returnM=false'
                getdrivetime = requests.get(drivetimeurl)

            else:
                drivetimegeom = []
                staffingtotal = ""
                for fireStation in stationlist:
                    # staffing
                    assetlist = Staffing.objects.filter(firestation_id=fireStation.id)
                    stationstafftotal = 0
                    for staff in assetlist:
                        stationstafftotal = stationstafftotal + staff.personnel

                    if stationstafftotal <= 0:
                        continue

                    # geometry
                    stationasset = {}
                    stationasset["spatialReference"] = {"wkid": 4326}
                    stationasset["y"] = round(fireStation.geom.y, 5)
                    stationasset["x"] = round(fireStation.geom.x, 5)
                    stationgeom = {}
                    stationgeom["geometry"] = stationasset
                    drivetimegeom.append(stationgeom)
                    staffingtotal = staffingtotal + str(stationstafftotal) + ','

                drivepostdata = {}
                drivepostdata['f'] = 'pjson'
                drivepostdata['returnZ'] = False
                drivepostdata['returnM'] = False
                drivepostdata['env:outSR'] = 4326
                drivepostdata['text_input'] = staffingtotal[:-1]
                drivepostfeatures = {}
                drivepostfeatures['features'] = drivetimegeom
                drivepostfeatures['geometryType'] = "esriGeometryPoint"
                drivepostdata['Facilities'] = json.dumps(drivepostfeatures)

                # need to run async so it doesn't time out
                # getdrivetime = requests.post("http://gis.iaff.org/arcgis/rest/services/Production/PeopleCountOct2012/GPServer/PeopleCountOct2012/execute", data=drivepostdata)
                getdrivetime = requests.post("http://gis.iaff.org/arcgis/rest/services/Production/PeopleCount2017_V2/GPServer/PeopleCount2017/submitJob", data=drivepostdata)

            get_async_efff_service_status(json.loads(getdrivetime.content)['jobId'], dept[0])

        except KeyError:
            print 'Drive Time Failed for ' + dept[0].name

        except IntegrityError:
            print 'Drive Time Failed for ' + dept[0].name

        except Exception:
            print 'Drive Time Failed for ' + dept[0].name


def update_parcel_effectivefirefighting_table(drivetimegeom, department):
    """
    Intersect with Parcel layer and update parcel_department_hazard_level table
    """

    # drivetimegeomLT15 = None
    drivetimegeomLT27 = None
    drivetimegeomLT42 = None
    drivetimegeomGT38 = None
    drivetimegeomGT41 = None

    for responseJSON in drivetimegeom:
        if arcgis2geojson(responseJSON['geometry'])['type'] == 'MultiPolygon':
            responsegeom = GEOSGeometry(json.dumps(arcgis2geojson(responseJSON['geometry'])))
        else:
            responsegeom = GEOSGeometry(MultiPolygon(fromstr(str(arcgis2geojson(responseJSON['geometry']))),))

        # Dissolve/Union Geometry
        # if(responseJSON['attributes']['SUM_StaffLong'] < 15):
        #     if drivetimegeomLT15 is None:
        #         drivetimegeomLT15 = responsegeom
        #     else:
        #         drivetimegeomLT15 = drivetimegeomLT15.union(responsegeom)
        if(responseJSON['attributes']['SUM_StaffLong'] > 14):
            if drivetimegeomLT27 is None:
                drivetimegeomLT27 = responsegeom
            else:
                drivetimegeomLT27 = drivetimegeomLT27.union(responsegeom)
        if(responseJSON['attributes']['SUM_StaffLong'] > 26):
            if drivetimegeomLT42 is None:
                drivetimegeomLT42 = responsegeom
            else:
                drivetimegeomLT42 = drivetimegeomLT42.union(responsegeom)
        if(responseJSON['attributes']['SUM_StaffLong'] > 38):
            if drivetimegeomGT38 is None:
                drivetimegeomGT38 = responsegeom
            else:
                drivetimegeomGT38 = drivetimegeomGT38.union(responsegeom)
        if(responseJSON['attributes']['SUM_StaffLong'] > 41):
            if drivetimegeomGT41 is None:
                drivetimegeomGT41 = responsegeom
            else:
                drivetimegeomGT41 = drivetimegeomGT41.union(responsegeom)

    cursor = connections['nfirs'].cursor()
    QUERY_INTERSECT_FOR_PARCEL_DRIVETIME = """SELECT sum(case when l.risk_category = 'Low' THEN 1 ELSE 0 END) as low,
        sum(CASE WHEN l.risk_category = 'Medium' THEN 1 ELSE 0 END) as medium,
        sum(CASE WHEN l.risk_category = 'High' THEN 1 ELSE 0 END) high,
        sum(CASE WHEN l.risk_category is null THEN 1 ELSE 0 END) as unknown
        FROM parcel_risk_category_local l
        JOIN (SELECT ST_SetSRID(ST_GeomFromGeoJSON(%(drive_geom)s), 4326) as drive_geom) x
        ON drive_geom && l.wkb_geometry
        WHERE ST_WITHIN(l.wkb_geometry, drive_geom)
        """

    # option to limit dept track and ST_WITHIN(l.wkb_geometry, %(owned_geom)s)
    # option to collect info on 0 14 personnel fighting force
    # saving overhead because under 15 isn't used right now - would have to add database entry below
    # if drivetimegeomLT15:
    #   cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomLT15.json, 'owned_geom': department.geom.wkb})
    #   results0 = dictfetchall(cursor)
    if drivetimegeomLT27:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomLT27.intersection(department.owned_tracts_geom).json, 'owned_geom': department.owned_tracts_geom.wkb})
        results15 = dictfetchall(cursor)
        if results15:
            if results15[0]['unknown'] is None:
                results15[0]['unknown'] = 0
            if results15[0]['low'] is None:
                results15[0]['low'] = 0
    if drivetimegeomLT42:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomLT42.intersection(department.owned_tracts_geom).json, 'owned_geom': department.owned_tracts_geom.wkb})
        results27 = dictfetchall(cursor)
        if results27:
            if results27[0]['medium'] is None:
                results27[0]['medium'] = 0
    if drivetimegeomGT38:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomGT38.intersection(department.owned_tracts_geom).json, 'owned_geom': department.owned_tracts_geom.wkb})
        results38 = dictfetchall(cursor)
        if results38:
            if results38[0]['high'] is None:
                results38[0]['high'] = 0
    if drivetimegeomGT41:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomGT41.intersection(department.owned_tracts_geom).json, 'owned_geom': department.owned_tracts_geom.wkb})
        results42 = dictfetchall(cursor)
        if results15:
            if results42[0]['high'] is None:
                results42[0]['high'] = 0

    # Overwrite/Update efff area if already loaded
    if EffectiveFireFightingForceLevel.objects.filter(department_id=department.id):
        existingrecord = EffectiveFireFightingForceLevel.objects.filter(department_id=department.id)
        addefffdepartment = existingrecord[0]

        # there is an 'all' value for future calculations on the total
        addefffdepartment.perc_covered_low_15_26 = 0
        addefffdepartment.perc_covered_unknown_15_26 = 0
        addefffdepartment.perc_covered_medium_27_42 = 0
        addefffdepartment.perc_covered_high38_plus = 0
        addefffdepartment.perc_covered_high_43_plus = 0

        if drivetimegeomLT27:
            addefffdepartment.parcelcount_low_15_26 = results15[0]['low']
            addefffdepartment.parcelcount_unknown_15_26 = results15[0]['unknown']
            addefffdepartment.perc_covered_low_15_26 = round(100 * (float(results15[0]['low']) / float(department.metrics.structure_counts_by_risk_category.low)), 2)
            addefffdepartment.perc_covered_unknown_15_26 = round(100 * (float(results15[0]['unknown']) / float(department.metrics.structure_counts_by_risk_category.unknown)), 2)

            if isinstance(drivetimegeomLT27, MultiPolygon):
                addefffdepartment.drivetimegeom_15_26 = drivetimegeomLT27
            else:
                addefffdepartment.drivetimegeom_15_26 = MultiPolygon(drivetimegeomLT27)
        if drivetimegeomLT42:
            addefffdepartment.parcelcount_medium_27_42 = results27[0]['medium']
            addefffdepartment.perc_covered_medium_27_42 = round(100 * (float(results27[0]['medium']) / float(department.metrics.structure_counts_by_risk_category.medium)), 2)
            if isinstance(drivetimegeomLT42, MultiPolygon):
                addefffdepartment.drivetimegeom_27_42 = drivetimegeomLT42
            else:
                addefffdepartment.drivetimegeom_27_42 = MultiPolygon(drivetimegeomLT42)
        if drivetimegeomGT38:
            addefffdepartment.parcelcount_high38_plus = results38[0]['high']
            addefffdepartment.perc_covered_high38_plus = round(100 * (float(results38[0]['high']) / float(department.metrics.structure_counts_by_risk_category.high)), 2)
            if isinstance(drivetimegeomGT38, MultiPolygon):
                addefffdepartment.drivetimegeom_38_plus = drivetimegeomGT38
            else:
                addefffdepartment.drivetimegeom_38_plus = MultiPolygon(drivetimegeomGT38)
        if drivetimegeomGT41:
            addefffdepartment.parcelcount_high_43_plus = results42[0]['high']
            addefffdepartment.perc_covered_high_43_plus = round(100 * (float(results42[0]['high']) / float(department.metrics.structure_counts_by_risk_category.high)), 2)
            if isinstance(drivetimegeomGT41, MultiPolygon):
                addefffdepartment.drivetimegeom_43_plus = drivetimegeomGT41
            else:
                addefffdepartment.drivetimegeom_43_plus = MultiPolygon(drivetimegeomGT41)

        print department.name + " EFFF Area Updated" + ' at ' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    else:
        deptefffarea = {}
        deptefffarea['department'] = department
        deptefffarea['perc_covered_low_15_26'] = 0
        deptefffarea['perc_covered_unknown_15_26'] = 0
        deptefffarea['perc_covered_medium_27_42'] = 0
        deptefffarea['perc_covered_high38_plus'] = 0
        deptefffarea['perc_covered_high_43_plus'] = 0

        if drivetimegeomLT27:
            deptefffarea['parcelcount_low_15_26'] = results15[0]['low']
            deptefffarea['parcelcount_unknown_15_26'] = results15[0]['unknown']
            deptefffarea['perc_covered_low_15_26'] = round(100 * (float(results15[0]['low']) / float(department.metrics.structure_counts_by_risk_category.low)), 2)
            deptefffarea['perc_covered_unknown_15_26'] = round(100 * (float(results15[0]['unknown']) / float(department.metrics.structure_counts_by_risk_category.unknown)), 2)
            if isinstance(drivetimegeomLT27, MultiPolygon):
                deptefffarea['drivetimegeom_15_26'] = drivetimegeomLT27
            else:
                deptefffarea['drivetimegeom_15_26'] = MultiPolygon(drivetimegeomLT27)
        if drivetimegeomLT42:
            deptefffarea['parcelcount_medium_27_42'] = results27[0]['medium']
            deptefffarea['perc_covered_medium_27_42'] = round(100 * (float(results27[0]['medium']) / float(department.metrics.structure_counts_by_risk_category.medium)), 2)
            if isinstance(drivetimegeomLT42, MultiPolygon):
                deptefffarea['drivetimegeom_27_42'] = drivetimegeomLT42
            else:
                deptefffarea['drivetimegeom_27_42'] = MultiPolygon(drivetimegeomLT42)
        if drivetimegeomGT38:
            deptefffarea['parcelcount_high38_plus'] = results38[0]['high']
            deptefffarea['perc_covered_high38_plus'] = round(100 * (float(results38[0]['high']) / float(department.metrics.structure_counts_by_risk_category.high)), 2)
            if isinstance(drivetimegeomGT38, MultiPolygon):
                deptefffarea['drivetimegeom_38_plus'] = drivetimegeomGT38
            else:
                deptefffarea['drivetimegeom_38_plus'] = MultiPolygon(drivetimegeomGT38)
        if drivetimegeomGT41:
            deptefffarea['parcelcount_high_43_plus'] = results42[0]['high']
            deptefffarea['perc_covered_high_43_plus'] = round(100 * (float(results42[0]['high']) / float(department.metrics.structure_counts_by_risk_category.high)), 2)
            if isinstance(drivetimegeomGT41, MultiPolygon):
                deptefffarea['drivetimegeom_43_plus'] = drivetimegeomGT41
            else:
                deptefffarea['drivetimegeom_43_plus'] = MultiPolygon(drivetimegeomGT41)

        addefffdepartment = EffectiveFireFightingForceLevel.objects.create(**deptefffarea)
        print department.name + " EFFF Area Created" + ' at ' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    addefffdepartment.save()
