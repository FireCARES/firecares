import json
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from pymongo import MongoClient
from firecares.firestation.models import FireStation


class Command(BaseCommand):
    help = 'Loads Fire District boundaries from mongo.'
    args = '<department>'
    option_list = BaseCommand.option_list + (
        make_option('-m', '--mongo-client',
                    dest='client',
                    default='localhost',
                    help='MongoDB client.'),
        make_option('-d', '--department',
                    dest='department',
                    help='The FireCARES department id.'),
    )

    def handle(self, *args, **options):

        department = options.get('department')
        mongo_client = options.get('client')
        port = 27017
        stations = FireStation.objects.filter(department=department,
                                              district__isnull=True,
                                              geom__isnull=False)

        if not department:
            raise CommandError('A department id must be provided.')

        with MongoClient(mongo_client, port) as client:
            db = client.harvester
            districts = db['fire_districts']

            for station in stations:
                matches = districts.find({
                "feature.geometry": {
                    "$geoIntersects": {
                    "$geometry": json.loads(station.geom.json)
                        }
                    },
                })
                if matches.count() == 1:
                    self.stdout.write('Exactly one match found for station id: {0}.  Updating.'.format(station.id))
                    match = matches.next()
                    geom = GEOSGeometry(json.dumps(match['feature']['geometry']))

                    if geom.geom_type == 'Polygon':
                        geom = MultiPolygon([geom])
                    elif geom.geom_type == 'MultiPolygon':
                        pass
                    else:
                        raise CommandError('Unhandled geometry type: {0}'.format(geom.geom_type))

                    station.district = geom
                    station.save()

                elif matches.count() == 0:
                    self.stdout.write('No matches!')


