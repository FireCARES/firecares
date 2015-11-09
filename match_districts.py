import sys
import os
import django
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon, Polygon
from firecares.firestation.models import FireStation

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firecares.settings.local")
django.setup()

num_command_args = len(sys.argv)
if num_command_args < 3:
    assert ('Expected command line args: <path to geojson file> <state to filter stations>')
geojson_file = sys.argv[1]
state_filter = sys.argv[2]
ds = DataSource(geojson_file)
filter_stations = FireStation.objects.filter(state=state_filter)

if filter_stations is None:
    assert( 'Could not filter stations')

for layer in ds:
    geom_list = layer.get_geoms(geos=True)
    num_geoms = len(geom_list)
    print 'Num Districts: {0}'.format(num_geoms)
    for geom in geom_list:
        match_stations = list()

        for station in filter_stations:
            if geom.intersects(station.geom) == True:
                match_stations.append(station)

        matched_station = None
        num_match_stations = len(match_stations)
        if num_match_stations == 1:
            matched_station = match_stations[0]
        elif num_match_stations > 1:
            geom.set_srid(4326)
            meter_geom = geom.centroid.transform(3857,clone=True)
            shortest_dist = meter_geom.distance(match_stations[0].geom.centroid.transform(3857,clone=True))
            for station in match_stations:
               station_dist = meter_geom.distance(station.geom.centroid.transform(3857,clone=True))
               if station_dist < shortest_dist:
                   shortest_dist = station_dist
                   matched_station = station

        if matched_station is not None and matched_station.district is None:
            print 'matched district for {0}'.format(matched_station.name)
            if isinstance(geom,MultiPolygon):
                matched_station.district = geom
            elif isinstance(geom,Polygon):
                matched_station.district = MultiPolygon(geom)
            matched_station.save()
        elif matched_station is not None and matched_station.district is not None:
            print matched_station.district.centroid



