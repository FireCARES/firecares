import json
import requests
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from collections import OrderedDict
from django.contrib.gis.geos import GeometryCollection

validate_endpoint = 'http://geojsonlint.com/validate'


class Command(BaseCommand):
    help = 'Dumps a FireDepartment into GeoJSON'

    def add_arguments(self, parser):
        parser.add_argument('firedepartment_id', nargs='+', type=int)

    def handle(self, *args, **options):

        for department in options.get('firedepartment_id'):
            try:
                department = FireDepartment.objects.get(id=department)
            except FireDepartment.DoesNotExist:
                print 'Fire Department with id {0} not found.'.format(department)
                return
            print 'Dumping GeoJSON for: {0}.'.format(department.name)

            feature_collection = []
            feature = {'type': 'Feature', 'geometry': GeometryCollection([department.headquarters_address.geom])}

            if department.geom:
                feature['geometry'].append(department.geom)

            feature['properties'] = OrderedDict(id=department.id,
                                                fdid=department.fdid,
                                                name=department.name,
                                                address_line1=department.headquarters_address.address_line1,
                                                address_line2=department.headquarters_address.address_line2,
                                                department_type=department.department_type,
                                                organization_type=department.organization_type,
                                                website=department.website,
                                                region=department.region,
                                                city=department.headquarters_address.city,
                                                state=department.headquarters_address.state_province,
                                                postal_code=department.headquarters_address.postal_code,
                                                country=department.headquarters_address.country.iso_code,
                                                stations=[station.id for station in department.firestation_set.all()],
                                                )

            feature['geometry'] = json.loads(feature['geometry'].json)
            feature_collection.append(feature)

        with open('us-{0}-{1}-departments_nfors.geojson'.format(department.state.lower(),
                                                                department.name.lower().replace(' ', '_')), 'w') as features:
            coll = json.dumps({'type': 'FeatureCollection', 'features': feature_collection, "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}}, indent=4)
            features.write(coll)
            good_request = requests.post(validate_endpoint, data=coll)
            print good_request.json()
