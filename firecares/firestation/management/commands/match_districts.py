import sys
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import MultiPolygon, Polygon
from firecares.firestation.models import FireStation
from optparse import make_option

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Matches district geometry within GeoJSON files with appropriate fire station.'
    queryset = None
    def set_queryset(self, station_queryset):
        if station_queryset is not None:
            self.queryset = station_queryset

    def add_arguments(self, parser):
        parser.add_argument('geojson_file')
        parser.add_argument('verbose',default=False,nargs='?')

    def handle(self, *args, **options):
        geojson_file = options.get('geojson_file')
        verbose = options.get('verbose')
        state_filter = geojson_file.split('/')[-1].split('-')[1]
        ds = DataSource(geojson_file)
        print 'Extracted State code: {0}'.format(state_filter.upper())
        filter_stations = self.queryset
        if filter_stations is None:
            filter_stations = FireStation.objects.filter(state=state_filter.upper())

        if filter_stations is None:
            assert( 'Could not filter stations')

        for layer in ds:
            geom_list = layer.get_geoms(geos=True)
            num_geoms = len(geom_list)
            num_updated = 0
            print 'Number of Districts: {0}'.format(num_geoms)
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
                    if verbose:
                        print 'Updated district for {0}'.format(matched_station.name)
                    if isinstance(geom,MultiPolygon):
                        matched_station.district = geom
                    elif isinstance(geom,Polygon):
                        matched_station.district = MultiPolygon(geom)
                    matched_station.save()
                    num_updated += 1
                elif matched_station is not None and matched_station.district is not None:
                    if verbose:
                        print 'District already set: No Update'

        print 'Successfully Updated {0}/{1} Stations'.format(num_updated,num_geoms)






