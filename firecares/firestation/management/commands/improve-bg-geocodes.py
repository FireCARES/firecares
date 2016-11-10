from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderQuotaExceeded, GeocoderTimedOut, GeocoderServiceError
from time import sleep
from django.db import connections
from django.contrib.gis.geos import GEOSGeometry, Point


class Command(BaseCommand):
    help = 'Identifies bad geocodes in a given 2010 block group.'

    def add_arguments(self, parser):
        parser.add_argument('block_group')

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do not execute update statements.',
        )

    def handle(self, block_group, *args, **options):
        g = GoogleV3()
        cursor = connections['nfirs'].cursor()

        cursor.execute('SET transform_null_equals TO ON;')
        select = """
        select state, fdid, num_mile, street_pre, streetname, streettype, streetsuf, city, state_id, zip5, zip4, state, a.geom, count(*)
        from incidentaddress a
        where bkgpidfp10=%s and fdid<>(select fdid from firestation_firedepartment where id in (select department_for_block_group(%s)))
        and geocodable is not false
        group by state, fdid, num_mile, street_pre, streetname, streettype, streetsuf, city, state_id, zip5, zip4, state, a.geom
        """

        cmd = cursor.mogrify(select, (block_group, block_group))
        print cmd
        cursor.execute(cmd)
        over_quota_exceptions = 0

        for res in cursor.fetchall():

            if over_quota_exceptions >= 10:
                raise GeocoderQuotaExceeded('Too many consecutive timeouts.')

            print 'Row: ', res
            state, fdid, num_mile, street_pre, streetname, streettype, streetsuf, city, state_id, zip5, zip4, state_abbreviation, geom, count = res


            update = '''
            update incidentaddress
            set geom=ST_GeomFromText('POINT({results.longitude} {results.latitude})', 4326)
            {where}
            '''

            where_clause = cursor.mogrify('''WHERE state=%s and fdid=%s and num_mile=%s and street_pre=%s and streetsuf=%s and city=%s
             and state_id=%s and zip4=%s and zip5=%s and streetname=%s''', (state, fdid, num_mile, street_pre,
                                                                           streetsuf, city, state_id, zip4, zip5,
                                                                           streetname))

            if state_id == 'OO':
                state_id = ''

            if zip5 == '00000':
                zip5 = ''

            query_string = ' '.join([n for n in [num_mile, street_pre, streetname, streettype, streetsuf, city, state_id or state, zip5] if n])

            try:
                fd = FireDepartment.objects.filter(fdid=fdid, state=state).first()
                bounds = None
                department_geom = None

                if fd:
                    department_geom = fd.geom or fd.headquarters_address.geom.buffer(.5)

                    if department_geom:
                        xmin, ymin, xmax, ymax = department_geom.extent
                        bounds = [ymin, xmin, ymax, xmax]

                results = g.geocode(query=query_string, bounds=bounds)

                if not results:
                    continue

                results_point = Point(results.longitude, results.latitude)

                if geom:
                    geom = GEOSGeometry(geom)

                    if department_geom:
                        distance_improvement = department_geom.centroid.distance(geom)-department_geom.centroid.distance(results_point)

                        if distance_improvement <= -1:
                            self.stdout.write('Not updating since {} is a negative distance improvement'.format(distance_improvement))
                            continue
                        else:
                            print 'Moving geometry from: {geom.x}, {geom.y} to {results.longitude}, {results.latitude}.'.format(geom=geom, results=results)
                            print 'Distance improvement: {}'.format(distance_improvement)

                if not options['dry_run']:
                    print update.format(results=results, where=where_clause)
                    cursor.execute(update.format(results=results, where=where_clause))

                self.stdout.write('{} rows updated'.format(cursor.rowcount))

            except GeocoderQuotaExceeded:
                self.stdout.write('Geocoding Quota exceeded.')
                over_quota_exceptions += 1
                sleep(1)
                continue
            except GeocoderTimedOut:
                self.stdout.write('Geocoder Timed Out.')
                sleep(1)
                continue
            except GeocoderServiceError:
                self.stdout.write('Geocoder Timed Out.')
                sleep(1)
                continue
            over_quota_exceptions = 0
            print '\n'

        cursor.execute('SET transform_null_equals TO OFF;')