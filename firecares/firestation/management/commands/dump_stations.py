import json
import requests
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from collections import OrderedDict
from django.contrib.gis.geos import GeometryCollection

validate_endpoint = 'http://geojsonlint.com/validate'


class Command(BaseCommand):
    help = 'Dumps the fire station into GeoJSON'

    def add_arguments(self, parser):
        parser.add_argument('firedepartment_id', nargs='+', type=int)

    def handle(self, *args, **options):

        for department in options.get('firedepartment_id'):
            try:
                fd = FireDepartment.objects.get(id=department)
            except FireDepartment.DoesNotExist:
                print 'Fire Department with id {0} not found.'.format(department)
                return
            print 'Dumping GeoJSON for: {0}.'.format(fd.name)

            feature_collection = []

            for station in fd.firestation_set.all():
                feature = {'type': 'Feature', 'geometry': GeometryCollection([station.geom])}

                staffing = []

                for staff in station.staffing_set.all():
                    staffing_dict = {}

                    for field in 'id apparatus firefighter firefighter_emt firefighter_paramedic' \
                                 ' ems_emt ems_paramedic officer officer_paramedic ems_supervisor ' \
                                 'chief_officer'.split():
                        staffing_dict[field] = getattr(staff, field)

                    staffing.append(staffing_dict)

                if station.district:
                    feature['geometry'].append(station.district)

                feature['properties'] = OrderedDict(id=station.id,
                                                    name=station.name,
                                                    address_line1=station.station_address.address_line1,
                                                    address_line2=station.station_address.address_line2,
                                                    city=station.station_address.city,
                                                    state=station.station_address.state_province,
                                                    postal_code=station.station_address.postal_code,
                                                    country=station.station_address.country.iso_code,
                                                    department=station.department.id,
                                                    staffing=staffing
                                                    )

                feature['geometry'] = json.loads(feature['geometry'].json)
                feature_collection.append(feature)

            with open('us-{0}-{1}-stations_nfors.geojson'.format(station.state.lower(), station.department.name.lower().replace(' ', '_')), 'w') as features:
                coll = json.dumps({'type': 'FeatureCollection', 'features': feature_collection, "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}}, indent=4)
                features.write(coll)
                good_request = requests.post(validate_endpoint, data=coll)
                print good_request.json()
