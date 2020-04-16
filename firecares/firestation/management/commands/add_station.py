from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment, FireStation
from firecares.firecares_core.models import Address
from django.db import transaction
from django.contrib.gis.geos import Point
from datetime import datetime


class Command(BaseCommand):
    help = 'Adds a firestation to the given department'

    def add_arguments(self, parser):
        parser.add_argument('firedepartment_id', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument('--address',
                            dest='address',
                            default=None,
                            help='Address of department')

        parser.add_argument('--name',
                            dest='name',
                            default=None,
                            help='Name of station')

        parser.add_argument('--number',
                            dest='number',
                            default=None,
                            help='Station number')

        parser.add_argument('--fdid',
                            dest='fdid',
                            default=None,
                            help='The stations FDID')

        parser.add_argument('--dryrun',
                            dest='dryrun',
                            default=False,
                            action='store_true',
                            help='Run as dry run')

    def handle(self, *args, **options):
        name = options.get('name')
        fdid = options.get('fdid')
        number = options.get('number')
        latitude = options.get('latitude')
        longitude = options.get('longitude')
        address = options.get('address')
        dryrun = options.get('dryrun')

        with transaction.atomic():
            for department in options.get('firedepartment_id'):
                try:
                    fd = FireDepartment.objects.get(id=department)
                except FireDepartment.DoesNotExist:
                    print 'Fire Department with id {0} not found.'.format(department)
                    return

                print address

                address = Address.create_from_string(address, dry_run=dryrun)
                if not address and not (latitude and longitude):
                    print 'Cannot lookup address, stopping.'
                    return

                geom = None

                if latitude and longitude:
                    geom = Point(longitude, latitude)
                else:
                    geom = address.geom

                if not dryrun:
                    station = FireStation.objects.create(name=name, fdid=fdid, station_number=number,
                                                         geom=geom, station_address=address, address=address.address_line1,
                                                         city=address.city, state=address.state_province,
                                                         zipcode=address.postal_code, department=fd,
                                                         source_datadesc='FireCARES add station command.',
                                                         loaddate=datetime.now(),
                                                         ftype='Emergency Response and Law Enforcement')

                    print 'station successfully created: {0}'.format(station.id)

                else:
                    print 'Create new FireStation with these params: {0}'.format(dict(name=name, fdid=fdid, station_number=number,
                                                                                      geom=geom, station_address=address, department=fd,
                                                                                      source_datadesc='FireCARES add station command.',
                                                                                      loaddate=datetime.now(),
                                                                                      ftype='Emergency Response and Law Enforcement'))
