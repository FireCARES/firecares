import traceback
from celery import chain, group
from firecares.celery import app

from django.contrib.gis.geos import GEOSGeometry
from django.db import connections
from django.db.utils import ConnectionDoesNotExist

from firecares.weather.models import (WeatherWarnings, DepartmentWarnings, StationWarnings)


@app.task(queue='weather-task', rate_limit='30/m')
def collect_weather_noaa_warnings(id, dry_run=False):
    """
    Updates department performance scores.
    """

    #cursor = connections['nfirs'].cursor()
    WeatherWarnings.load_data()

 

@app.task(queue='weather-task')
def update_department_for_warning(id):

    #TODO
    print "updating department {}".format(id)
    chain(update_nfirs_counts.si(id),
          update_performance_score.si(id),
          group(refresh_quartile_view_task.si(),
          refresh_national_calculations_view_task.si())).delay()


@app.task(queue='weather-task')
def calculate_department_intersect_geom(fd_id):
    """
    Calculate which Stations have weather updates

    TODO
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

