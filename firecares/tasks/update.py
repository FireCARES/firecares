import copy
import numpy as np
import traceback
import requests
import json
import time
from django.db.utils import IntegrityError
from firecares.utils.arcgis2geojson import arcgis2geojson
from celery import chain, group
from firecares.celery import app
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

    print "updating performance score for {}".format(id)

    try:
        cursor = connections['nfirs'].cursor()
        fd = FireDepartment.objects.get(id=id)
    except (ConnectionDoesNotExist, FireDepartment.DoesNotExist):
        return

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
    where a.state='%(state)s' and a.fdid='%(fdid)s' and prop_use in (''419'',''429'',''439'',''449'',''459'',''460'',''462'',''464'',''400'')
        and fire_sprd is not null and fire_sprd != ''''
    group by risk_category, fire_sprd
    order by risk_category, fire_sprd ASC')
    AS ct(risk_category text, "object_of_origin" bigint, "room_of_origin" bigint, "floor_of_origin" bigint, "building_of_origin" bigint, "beyond" bigint);
    """

    cursor.execute(RESIDENTIAL_FIRES_BY_FDID_STATE, {'fdid': fd.fdid, 'state': fd.state})

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
            print 'updating fdid: {2} - {3} performance score from: {0} to {1}.'.format(old_score, record.dist_model_score, fd.id, HazardLevels(record.level).name)

        except (NotEnoughRecords, ZeroDivisionError):
            print 'Error updating DIST score: {}.'.format(traceback.format_exc())
            record.dist_model_score = None

        if not dry_run:
            record.save()

    # Clear out scores for missing hazard levels
    if not dry_run:
        missing_categories = set(risk_mapping.keys()) - set(map(lambda x: x.get('risk_category'), results))
        for r in missing_categories:
            print 'clearing {0} level from {1} due to missing categories in aggregation'.format(r, fd.id)
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
        print 'updating fdid: {2} - {3} performance score from: {0} to {1}.'.format(old_score, record.dist_model_score, fd.id, HazardLevels(record.level).name)

    except (NotEnoughRecords, ZeroDivisionError):
        print 'Error updating DIST score: {}.'.format(traceback.format_exc())
        record.dist_model_score = None

    if not dry_run:
        record.save()

    print "...updated performance score for {}".format(id)


CIVILIAN_CASUALTIES = """SELECT count(1) as count, extract(year from a.inc_date) as year, COALESCE(y.risk_category, 'N/A') as risk_level
FROM joint_civiliancasualty a
LEFT JOIN
    (SELECT state, fdid, inc_date, inc_no, exp_no, x.parcel_id, x.risk_category
        FROM ( SELECT *
            FROM joint_incidentaddress a
            LEFT JOIN parcel_risk_category_local using (parcel_id)
        ) AS x
    ) AS y
USING (state, fdid, inc_date, inc_no, exp_no)
WHERE a.state = %(state)s AND a.fdid = %(fdid)s AND extract(year FROM a.inc_date) IN %(years)s
GROUP BY y.risk_category, extract(year from a.inc_date)
ORDER BY extract(year from a.inc_date) DESC"""


ALL_FIRE_CALLS = """SELECT count(1) as count, extract(year from b.inc_date) as year, COALESCE(y.risk_category, 'N/A') as risk_level
FROM joint_fireincident b
LEFT JOIN
    (SELECT state, fdid, inc_date, inc_no, exp_no, x.parcel_id, x.risk_category
        FROM (SELECT *
            FROM joint_incidentaddress a
            LEFT JOIN parcel_risk_category_local using (parcel_id)
        ) AS x
    ) AS y
USING (state, fdid, inc_date, inc_no, exp_no)
WHERE b.state = %(state)s AND b.fdid = %(fdid)s AND extract(year FROM b.inc_date) IN %(years)s
GROUP BY y.risk_category, extract(year FROM b.inc_date)
ORDER BY extract(year FROM b.inc_date) DESC"""


STRUCTURE_FIRES = """SELECT count(1) as count, extract(year from a.alarm) as year, COALESCE(y.risk_category, 'N/A') as risk_level
FROM joint_buildingfires a
LEFT JOIN
    (SELECT state, fdid, inc_date, inc_no, exp_no, x.parcel_id, x.risk_category
        FROM ( SELECT *
            FROM joint_incidentaddress a
            LEFT JOIN parcel_risk_category_local using (parcel_id)
        ) AS x
    ) AS y
USING (state, fdid, inc_date, inc_no, exp_no)
WHERE a.state = %(state)s AND a.fdid = %(fdid)s AND extract(year FROM a.inc_date) IN %(years)s
GROUP BY y.risk_category, extract(year from a.alarm)
ORDER BY extract(year from a.alarm) DESC"""


FIREFIGHTER_CASUALTIES = """SELECT count(1) as count, extract(year from a.inc_date) as year, COALESCE(y.risk_category, 'N/A') as risk_level
FROM joint_ffcasualty a
LEFT JOIN
    (SELECT state, fdid, inc_date, inc_no, exp_no, x.parcel_id, x.risk_category
        FROM ( SELECT *
            FROM joint_incidentaddress a
            LEFT JOIN parcel_risk_category_local using (parcel_id)
        ) AS x
    ) AS y
USING (state, fdid, inc_date, inc_no, exp_no)
WHERE a.state = %(state)s AND a.fdid = %(fdid)s AND extract(year FROM a.inc_date) IN %(years)s
GROUP BY y.risk_category, extract(year from a.inc_date)
ORDER BY extract(year from a.inc_date) DESC"""


@app.task(queue='update')
def update_department(id):
    print "updating department {}".format(id)
    chain(update_nfirs_counts.si(id),
          update_performance_score.si(id),
          get_parcel_department_hazard_level_rollup(id),
          group(refresh_quartile_view_task.si(),
          refresh_national_calculations_view_task.si())).delay()


@app.task(queue='update')
def update_nfirs_counts(id, year=None, stat=None):
    """
    Queries the NFIRS database for statistics.
    """

    if not id:
        return

    print "updating NFIRS counts for {}".format(id)

    try:
        fd = FireDepartment.objects.get(id=id)
        cursor = connections['nfirs'].cursor()

    except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
        return

    mapping = {'Low': 1, 'Medium': 2, 'High': 4, 'N/A': 5}

    years = {}
    if not year:
        # get a list of years populated in the NFIRS database
        years_query = "select distinct(extract(year from inc_date)) as year from joint_buildingfires;"
        cursor.execute(years_query)
        # default years to None
        years = {x: {1: None, 2: None, 4: None, 5: None} for x in [int(n[0]) for n in cursor.fetchall()]}
    else:
        years = {y: {1: None, 2: None, 4: None, 5: None} for y in year}

    params = dict(fdid=fd.fdid, state=fd.state, years=tuple(years.keys()))

    queries = (
        ('civilian_casualties', CIVILIAN_CASUALTIES, params),
        ('residential_structure_fires', STRUCTURE_FIRES, params),
        ('firefighter_casualties', FIREFIGHTER_CASUALTIES, params),
        ('fire_calls', ALL_FIRE_CALLS, params)
    )

    if stat:
        queries = filter(lambda x: x[0] == stat, queries)

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

    print "...updated NFIRS counts for {}".format(id)


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
        print 'No census geom - {} ({})'.format(fd.name, fd.id)


@app.task(queue='update', rate_limit='5/h')
def refresh_quartile_view_task(*args, **kwargs):
    """
    Updates the Quartile Materialized Views.
    """

    print "updating quartile view"
    refresh_quartile_view()


@app.task(queue='update', rate_limit='5/h')
def refresh_national_calculations_view_task(*args, **kwargs):
    """
    Updates the National Calculation View.
    """

    print "updating national calculations view"
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


@app.task(queue='servicearea')
def create_parcel_department_hazard_level_rollup_all():
    """
    Task for updating the servicearea table rolling up parcel hazard categories with departement drive time data
    """
    for fd in FireDepartment.objects.all():
        get_parcel_department_hazard_level_rollup(fd.id)


def get_parcel_department_hazard_level_rollup(fd_id):
    """
    Update for one department for the drive time hazard level
    """
    stationlist = FireStation.objects.filter(department_id=fd_id)
    dept = FireDepartment.objects.filter(id=fd_id)

    print "Calculating Drive times for:  " + dept[0].name

    #  Use Headquarters geometry if there is no Statffing assets
    if len(stationlist) < 1:
        drivetimeurl = 'https://geo.firecares.org/?f=json&Facilities={"features":[{"geometry":{"x":' + str(dept[0].headquarters_geom.x) + ',"spatialReference":{"wkid":4326},"y":' + str(dept[0].headquarters_geom.y) + '}}],"geometryType":"esriGeometryPoint"}&env:outSR=4326&text_input=4&Break_Values=4 6 8&returnZ=false&returnM=false'
        getdrivetime = requests.get(drivetimeurl)

    else:
        drivetimegeom = []
        for fireStation in stationlist:
            stationasset = {}
            stationasset["spatialReference"] = {"wkid": 4326}
            stationasset["y"] = round(fireStation.geom.y, 5)
            stationasset["x"] = round(fireStation.geom.x, 5)
            stationgeom = {}
            stationgeom["geometry"] = stationasset
            drivetimegeom.append(stationgeom)

        drivepostdata = {}
        drivepostdata['f'] = 'pjson'
        drivepostdata['returnZ'] = False
        drivepostdata['returnM'] = False
        drivepostdata['env:outSR'] = 4326
        drivepostdata['Break_Values'] = '4 6 8'
        drivepostfeatures = {}
        drivepostfeatures['features'] = drivetimegeom
        drivepostfeatures['geometryType'] = "esriGeometryPoint"
        drivepostdata['Facilities'] = json.dumps(drivepostfeatures)

        # GET URL (timing out)
        # getdrivetime = requests.post("http://test.firecares.org/service-area/?", data=drivepostdata)
        getdrivetime = requests.post("http://gis.iaff.org/arcgis/rest/services/Production/101ServerServiceAreaOct2012/GPServer/101ServerServiceAreaOct2012/execute", data=drivepostdata)

    try:
        update_parcel_department_hazard_level(json.loads(getdrivetime.content)['results'][0]['value']['features'], dept[0])

    except KeyError:
        print 'Drive Time Failed for ' + dept[0].name

    except IntegrityError:
        print 'Drive Time Failed for ' + dept[0].name

    except:
        print 'Drive Time Failed for ' + dept[0].name


def update_parcel_department_hazard_level(drivetimegeom, department):
    """
    Intersect with Parcel layer and update parcel_department_hazard_level table
    0-4 minutes
    4-6 minutes
    6-8 minutes
    """

    drivetimegeom0 = arcgis2geojson(drivetimegeom[2]['geometry'])
    drivetimegeom4 = arcgis2geojson(drivetimegeom[1]['geometry'])
    drivetimegeom6 = arcgis2geojson(drivetimegeom[0]['geometry'])

    cursor = connections['nfirs'].cursor()

    # TESTGEOM = "SELECT ST_AREA(ST_GeomFromGeoJSON(%(drive_geom)s),false) As area"
    QUERY_INTERSECT_FOR_PARCEL_DRIVETIME = """SELECT sum(case when l.risk_category = 'Low' THEN 1 ELSE 0 END) as low,
        sum(CASE WHEN l.risk_category = 'Medium' THEN 1 ELSE 0 END) as medium,
        sum(CASE WHEN l.risk_category = 'High' THEN 1 ELSE 0 END) high,
        sum(CASE WHEN l.risk_category is null THEN 1 ELSE 0 END) as unknown
        FROM parcel_risk_category_local l
        JOIN (SELECT ST_SetSRID(ST_GeomFromGeoJSON(%(drive_geom)s), 4326) as drive_geom) x
        ON drive_geom && l.wkb_geometry
        WHERE ST_WITHIN(l.wkb_geometry, drive_geom)
        """

    cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': json.dumps(drivetimegeom0)})
    results0 = dictfetchall(cursor)
    cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': json.dumps(drivetimegeom4)})
    results4 = dictfetchall(cursor)
    cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': json.dumps(drivetimegeom6)})
    results6 = dictfetchall(cursor)

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

        if drivetimegeom0['type'] == 'MultiPolygon':
            addhazardlevelfordepartment.drivetimegeom_0_4 = GEOSGeometry(json.dumps(drivetimegeom0))
        else:
            addhazardlevelfordepartment.drivetimegeom_0_4 = GEOSGeometry(MultiPolygon(fromstr(str(drivetimegeom0)),))
        if drivetimegeom4['type'] == 'MultiPolygon':
            addhazardlevelfordepartment.drivetimegeom_4_6 = GEOSGeometry(json.dumps(drivetimegeom4))
        else:
            addhazardlevelfordepartment.drivetimegeom_4_6 = GEOSGeometry(MultiPolygon(fromstr(str(drivetimegeom4)),))
        if drivetimegeom6['type'] == 'MultiPolygon':
            addhazardlevelfordepartment.drivetimegeom_6_8 = GEOSGeometry(json.dumps(drivetimegeom6))
        else:
            addhazardlevelfordepartment.drivetimegeom_6_8 = GEOSGeometry(MultiPolygon(fromstr(str(drivetimegeom6)),))

        print department.name + " Service Area Updated"
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

        if drivetimegeom0['type'] == 'MultiPolygon':
            deptservicearea['drivetimegeom_0_4'] = GEOSGeometry(json.dumps(drivetimegeom0))
        else:
            deptservicearea['drivetimegeom_0_4'] = GEOSGeometry(MultiPolygon(fromstr(str(drivetimegeom0)),))
        if drivetimegeom4['type'] == 'MultiPolygon':
            deptservicearea['drivetimegeom_4_6'] = GEOSGeometry(json.dumps(drivetimegeom4))
        else:
            deptservicearea['drivetimegeom_4_6'] = GEOSGeometry(MultiPolygon(fromstr(str(drivetimegeom4)),))
        if drivetimegeom6['type'] == 'MultiPolygon':
            deptservicearea['drivetimegeom_6_8'] = GEOSGeometry(json.dumps(drivetimegeom6))
        else:
            deptservicearea['drivetimegeom_6_8'] = GEOSGeometry(MultiPolygon(fromstr(str(drivetimegeom6)),))

        addhazardlevelfordepartment = ParcelDepartmentHazardLevel.objects.create(**deptservicearea)
        print department.name + " Service Area Created"

    addhazardlevelfordepartment.save()


@app.task(queue='servicearea')
def create_effective_firefighting_rollup_all():
    """
    Task for updating the effective fire fighting force EffectiveFireFightingForceLevel table
    """
    for fd in FireDepartment.objects.all():
        update_parcel_department_effectivefirefighting_rollup(fd.id)


def get_async_efff_service_status(jobid, dept_name):
    """
    Check status for Drive Time Asynchronous Webservice until there is a results value then call the results url to get json geom
    results: {
        PeopleCount: {
        paramUrl: "results/PeopleCount
    """
    getdrivetimejobstatus = requests.get("http://gis.iaff.org/arcgis/rest/services/Production/PeopleCount2017_V2/GPServer/PeopleCount2017/jobs/" + jobid + "?f=json")

    if 'results' in json.loads(getdrivetimejobstatus.content):
        print "Drive Time Analysis finished for " + dept_name.name
        drivetimejobfinished = requests.get("http://gis.iaff.org/arcgis/rest/services/Production/PeopleCount2017_V2/GPServer/PeopleCount2017/jobs/" + jobid + "/results/PeopleCount?f=pjson")
        update_parcel_effectivefirefighting_table(json.loads(drivetimejobfinished.content)['value']['features'], dept_name)

    else:
        print "Drive Time Analysis processing for " + dept_name.name
        time.sleep(20)
        get_async_efff_service_status(jobid, dept_name)


def update_parcel_department_effectivefirefighting_rollup(fd_id):
    """
    Update for one department for the effective fire fighting force
    """
    stationlist = FireStation.objects.filter(department_id=fd_id)
    dept = FireDepartment.objects.filter(id=fd_id)
    staffingtotal = "1"  # assume staffing minimum of 1 for now

    if dept[0].geom is None:

        print "No geometry for the department " + dept[0].name

    else:
        print "Calculating Response times and staffing for:  " + dept[0].name + ' at ' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

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

        try:
            get_async_efff_service_status(json.loads(getdrivetime.content)['jobId'], dept[0])

        except KeyError:
            print 'Drive Time Failed for ' + dept[0].name

        except IntegrityError:
            print 'Drive Time Failed for ' + dept[0].name

        except:
            print 'Drive Time Failed for ' + dept[0].name


def update_parcel_effectivefirefighting_table(drivetimegeom, department):
    """
    Intersect with Parcel layer and update parcel_department_hazard_level table
    """

    drivetimegeomLT15 = None
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

    drivetimegeomLT27 = drivetimegeomLT27.intersection(department.geom)
    drivetimegeomLT42 = drivetimegeomLT27.intersection(department.geom)
    drivetimegeomGT38 = drivetimegeomLT27.intersection(department.geom)
    drivetimegeomGT41 = drivetimegeomLT27.intersection(department.geom)

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
    # if drivetimegeomLT15:
    #   cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomLT15.json, 'owned_geom': department.owned_tracts_geom.wkb})
    #   results0 = dictfetchall(cursor)
    if drivetimegeomLT27:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomLT27.json, 'owned_geom': department.geom.wkb})
        results15 = dictfetchall(cursor)
    if drivetimegeomLT42:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomLT42.json, 'owned_geom': department.geom.wkb})
        results27 = dictfetchall(cursor)
    if drivetimegeomGT38:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomGT38.json, 'owned_geom': department.geom.wkb})
        results38 = dictfetchall(cursor)
    if drivetimegeomGT41:
        cursor.execute(QUERY_INTERSECT_FOR_PARCEL_DRIVETIME, {'drive_geom': drivetimegeomGT41.json, 'owned_geom': department.geom.wkb})
        results42 = dictfetchall(cursor)

    # Overwrite/Update efff area if already loaded
    if EffectiveFireFightingForceLevel.objects.filter(department_id=department.id):
        existingrecord = EffectiveFireFightingForceLevel.objects.filter(department_id=department.id)
        addefffdepartment = existingrecord[0]
        if drivetimegeomLT15:
            if isinstance(drivetimegeomLT15, MultiPolygon):
                addefffdepartment.drivetimegeom_014 = drivetimegeomLT15
            else:
                addefffdepartment.drivetimegeom_014 = MultiPolygon(drivetimegeomLT15)
        if drivetimegeomLT27:
            addefffdepartment.parcelcount_low_15_26 = results15[0]['low']
            addefffdepartment.parcelcount_unknown_15_26 = results15[0]['unknown']
            if isinstance(drivetimegeomLT27, MultiPolygon):
                addefffdepartment.drivetimegeom_15_26 = drivetimegeomLT27
            else:
                addefffdepartment.drivetimegeom_15_26 = MultiPolygon(drivetimegeomLT27)
        if drivetimegeomLT42:
            addefffdepartment.parcelcount_medium_27_42 = results27[0]['medium']
            if isinstance(drivetimegeomLT42, MultiPolygon):
                addefffdepartment.drivetimegeom_27_42 = drivetimegeomLT42
            else:
                addefffdepartment.drivetimegeom_27_42 = MultiPolygon(drivetimegeomLT42)
        if drivetimegeomGT38:
            addefffdepartment.parcelcount_high38_plus = results38[0]['high']
            if isinstance(drivetimegeomGT38, MultiPolygon):
                addefffdepartment.drivetimegeom_38_plus = drivetimegeomGT38
            else:
                addefffdepartment.drivetimegeom_38_plus = MultiPolygon(drivetimegeomGT38)
        if drivetimegeomGT41:
            addefffdepartment.parcelcount_high_43_plus = results42[0]['high']
            if isinstance(drivetimegeomGT41, MultiPolygon):
                addefffdepartment.drivetimegeom_43_plus = drivetimegeomGT41
            else:
                addefffdepartment.drivetimegeom_43_plus = MultiPolygon(drivetimegeomGT41)

        print department.name + " EFFF Area Updated" + ' at ' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

    else:
        deptefffarea = {}
        deptefffarea['department'] = department
        if drivetimegeomLT15:
            if isinstance(drivetimegeomLT15, MultiPolygon):
                deptefffarea['drivetimegeom_014'] = drivetimegeomLT15
            else:
                deptefffarea['drivetimegeom_014'] = MultiPolygon(drivetimegeomLT15)
        if drivetimegeomLT27:
            deptefffarea['parcelcount_low_15_26'] = results15[0]['low']
            deptefffarea['parcelcount_unknown_15_26'] = results15[0]['unknown']
            if isinstance(drivetimegeomLT27, MultiPolygon):
                deptefffarea['drivetimegeom_15_26'] = drivetimegeomLT27
            else:
                deptefffarea['drivetimegeom_15_26'] = MultiPolygon(drivetimegeomLT27)
        if drivetimegeomLT42:
            deptefffarea['parcelcount_medium_27_42'] = results27[0]['medium']
            if isinstance(drivetimegeomLT42, MultiPolygon):
                deptefffarea['drivetimegeom_27_42'] = drivetimegeomLT42
            else:
                deptefffarea['drivetimegeom_27_42'] = MultiPolygon(drivetimegeomLT42)
        if drivetimegeomGT38:
            deptefffarea['parcelcount_high38_plus'] = results38[0]['high']
            if isinstance(drivetimegeomGT38, MultiPolygon):
                deptefffarea['drivetimegeom_38_plus'] = drivetimegeomGT38
            else:
                deptefffarea['drivetimegeom_38_plus'] = MultiPolygon(drivetimegeomGT38)
        if drivetimegeomGT41:
            deptefffarea['parcelcount_high_43_plus'] = results42[0]['high']
            if isinstance(drivetimegeomGT41, MultiPolygon):
                deptefffarea['drivetimegeom_43_plus'] = drivetimegeomGT41
            else:
                deptefffarea['drivetimegeom_43_plus'] = MultiPolygon(drivetimegeomGT41)

        addefffdepartment = EffectiveFireFightingForceLevel.objects.create(**deptefffarea)
        print department.name + " EFFF Area Created"

    addefffdepartment.save()
