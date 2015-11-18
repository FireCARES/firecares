from django.contrib.gis.gdal import DataSource
from django.contrib.gis.measure import Distance as D
from firecares.firestation.models import FireStation, Staffing
import re
import importlib
from django.core.management.base import BaseCommand



class Command(BaseCommand):
    help = 'Updates fire station number and staffing from geojson file. Default algorithm splits total staff across each apparatus.'

    class Apparatus_Info():
        apparatus_name = 'Engine'
        apparatus_count = 0
        apparatus_staff_counts = list()
        def __init__(self,name):
            self.apparatus_name = name
            self.apparatus_count = 0
            self.apparatus_staff_counts = list()
        def Add(self,staff_count):
            self.apparatus_staff_counts.append(staff_count)
            self.apparatus_count += 1
        def Remove(self,staff_count):
            self.apparatus_staff_counts.remove(staff_count)
            self.apparatus_count -= 1
        def Clear(self):
            del self.apparatus_staff_counts[:]
            self.apparatus_count = 0
        def Print(self):
            print '{0} apparatus count: {1}'.format(self.apparatus_name,len(self.apparatus_staff_counts))

    def create_apparatus_info(self):
        apparatus_info_dict = dict()
        for apparatus_choice in Staffing.APPARATUS_CHOICES:
            apparatus_info_dict[apparatus_choice[0]]= Command.Apparatus_Info(apparatus_choice[0])
        return apparatus_info_dict

    def add_arguments(self, parser):
        parser.add_argument('geojson_file')
        parser.add_argument('--station_number_schema',dest='station_number_schema',nargs='?',default='ST_NO')
        parser.add_argument('--station_name_schema',dest='station_name_schema',nargs='?',default='Name')
        parser.add_argument('--total_staff_schema',dest='total_staff_schema',nargs='?',default='ST_FF')
        parser.add_argument('--station_address_schema',dest='station_address_schema',nargs='?',default='ADDRESS')
        parser.add_argument('--apparatus_schema',dest='apparatus_schema',nargs='?',\
                            default='Engine:Engine-Truck:Ladder/Truck/Aerial-Ladder:Ladder/Truck/Aerial-Rescue:Heavy Rescue-Quint:Quint-Ambulance:Ambulance/ALS-Chief:Chief',\
                            )
        parser.add_argument('--schema',default=None,dest='use_schema',nargs='?',help='Use schema file rather than command line',required=False)
        parser.add_argument('--verbose',action='store_true',default=False,dest='verbose',help='Turn on for more debug output')
        parser.add_argument('--no_geom', action='store_false', default=True, help='Use Geometry in Data Source as filter for matching',
                            dest='use_geometry_filter')
        parser.add_argument('--apparatus_counts', action='store_true', default=False, help='Use Apparatus field in Data Source as staff count for apparatus',
                            dest='use_apparatus_counts')


    def match_station(self,station_number,station_name,station_address,filter_stations):
        matched_station = None
        for station in filter_stations:
            extracted_station_number = re.search('Station (?P<station_num>\d+)',station.name)
            if extracted_station_number is not None:
                extracted_station_number = extracted_station_number.group('station_num')
                if station_number == station.station_number and extracted_station_number == station_number:
                    matched_station = station
                elif extracted_station_number == station_number:
                    matched_station = station
                else:
                    if station_address is None:
                        continue
                    address = station.station_address
                    if station_address == address:
                        print 'Address Match: {0}'.format(station.name)
                        matched_station = station

        if matched_station is not None:
            print 'Matched Name: {0}'.format(matched_station.name)
        else:
            print 'Could not match feature: {0}'.format(station_name)

        return matched_station

    def extract_apparatus_information(self,total_staff,apparatus_mapping_dict,feature,apparatus_info_dict,use_apparatus_counts):
        total_apparatus_count = 0
        apparatus_count_dict = dict()
        for apparatus_field,apparatus_map in apparatus_mapping_dict.iteritems():
            apparatus_count = feature.get(apparatus_field)
            if apparatus_count > 0:
                if verbose is True:
                    print '{0} count: {1}'.format(apparatus_field,apparatus_count)
                total_apparatus_count += 1
                apparatus_count_dict[apparatus_field] = apparatus_count

        i = 0

        for apparatus_field,apparatus_count in apparatus_count_dict.iteritems():
            if use_apparatus_counts is True:
                staff_count = apparatus_count
            else:
                staff_count = total_staff // total_apparatus_count
                if i == 0:
                    staff_count += total_staff % total_apparatus_count
            i += 1
            apparatus_map = apparatus_mapping_dict.get(apparatus_field,'Other')
            if apparatus_map == 'Chief':
                staff_count = 1
            if verbose is True:
                print 'Adding new {0} staff count of {1}'.format(apparatus_map,staff_count)
            apparatus_info = apparatus_info_dict[apparatus_map]
            apparatus_info.Add(staff_count)

    def create_staffing_from_dict(self,matched_station,apparatus_info_dict):
        for apparatus_choice,apparatus_info in apparatus_info_dict.iteritems():
            if len(apparatus_info.apparatus_staff_counts) > 0:
                for apparatus_count in apparatus_info.apparatus_staff_counts:
                    print 'Creating new {0} apparatus for {1} with {2} staff'.format(apparatus_choice,matched_station.name,apparatus_count)
                    staff_object = Staffing()
                    staff_object.apparatus = apparatus_choice
                    staff_object.firefighter = apparatus_count
                    staff_object.firestation = matched_station
                    matched_station.staffing_set.add(staff_object)
                    staff_object.save()



    def handle(self, *args, **options):

        geojson_file = options.get('geojson_file')
        verbose = options.get('verbose')
        schema_file = options.get('use_schema')
        state_filter = geojson_file.split('/')[-1].split('-')[1]
        ds = DataSource(geojson_file)
        print 'Extracted State code: {0}'.format(state_filter.upper())


        station_number_field = options.get('station_number_schema')
        station_name_field = options.get('station_name_schema')
        station_address_field = options.get('station_address_schema')
        total_staff_field = options.get('total_staff_schema')
        apparatus_list = options.get('apparatus_schema')

        use_geometry_filter = options.get('use_geometry_filter')
        use_apparatus_counts = options.get('use_apparatus_counts')

        apparatus_info_dict = self.create_apparatus_info()

        apparatus_mapping_dict = dict()
        apparatus_list = apparatus_list.split('-')
        for apparatus_pair in apparatus_list:
            apparatus_mapping = apparatus_pair.split(':')
            if verbose is True:
                print 'Apparatus pair: {0} : {1}'.format(apparatus_mapping[0],apparatus_mapping[1])
            apparatus_mapping_dict[apparatus_mapping[0]] = apparatus_mapping[1]

        filter_stations = FireStation.objects.filter(state=state_filter.upper())

        for layer in ds:
            if verbose is True:
                print 'Number of Features: {0}'.format(layer.num_feat)
            for feature in layer:
                for apparatus_info in apparatus_info_dict.itervalues():
                    apparatus_info.Clear()

                matched_station = None
                station_number = feature.get(station_number_field)
                station_name = feature.get(station_name_field)
                station_address = feature.get(station_address_field)
                total_staff = feature.get(total_staff_field)

                if total_staff < 1 and use_apparatus_counts is False:
                    continue

                print 'Total Staff: {0}'.format(total_staff)

                if use_geometry_filter is True:
                    filter_stations = FireStation.objects.filter(geom__distance_lte=(feature.geom.geos,D(mi=10)))

                if(isinstance(station_number,basestring)):
                    station_number = re.sub('[^0-9]','',station_number)
                else:
                    station_number = str(station_number)
                print 'Extracted station number: {0}'.format(station_number)

                matched_station = self.match_station(station_number,station_name,station_address,filter_stations)

                if matched_station is None:
                    continue

                self.extract_apparatus_information(total_staff,apparatus_mapping_dict,feature,apparatus_info_dict,use_apparatus_counts)

                self.create_staffing_from_dict(matched_station,apparatus_info_dict)
