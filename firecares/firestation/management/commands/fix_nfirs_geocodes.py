from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderQuotaExceeded, GeocoderTimedOut
from time import sleep
from django.db import connections
from django.contrib.gis.geos import GEOSGeometry, Point


class Command(BaseCommand):
    help = 'Updates the NFIRS statistics for a department'

    def add_arguments(self, parser):
        parser.add_argument('department', type=int)

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do not execute update statements.',
        )

        parser.add_argument(
            '--distance',
            dest='distance',
            default=2,
            type=float,
            help='Distance to look for bad geoms.',
        )

    def handle(self, department, *args, **options):
        g = GoogleV3()
        fd = FireDepartment.objects.get(id=department)

        cursor = connections['nfirs'].cursor()
        xmin, ymin, xmax, ymax = fd.geom.extent

        cursor.execute('SET transform_null_equals TO ON;')
        select = """
        select state, fdid, num_mile, street_pre, streetname, streettype, streetsuf, city, state_id, zip5, zip4, b.state_abbreviation, a.geom, count(*)
        from incidentaddress a
        inner join usgs_stateorterritoryhigh b
            on st_coveredby(a.geom, b.geom)
        where a.state=%s and a.fdid=%s and a.geom is not null and ((b.state_abbreviation!=a.state and a.state_id!=b.state_abbreviation) or (st_distance(a.geom, ST_GeomFromText(%s, 4326))>%s))
        group by state, fdid, num_mile, street_pre, streetname, streettype, streetsuf, city, state_id, zip5, zip4, b.state_abbreviation, a.geom
        HAVING count(*) >= 1
        order by count desc
        """

        cmd = cursor.mogrify(select, (fd.state, fd.fdid, fd.geom.centroid.wkt, options['distance']))
        print cmd
        cursor.execute(cmd)
        over_quota_exceptions = 0

        for res in cursor.fetchall():
            if over_quota_exceptions >= 10:
                self.stdout.write('Too many consecutive timeouts.')
                break

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

            geom = GEOSGeometry(geom)
            if state_id == 'OO':
                state_id = ''

            if zip5 == '00000':
                zip5 = ''

            query_string = ' '.join([n for n in [num_mile, street_pre, streetname, streettype, streetsuf, city, state_id or state, zip5] if n])

            try:
                results = g.geocode(query=query_string, bounds=[ymin, xmin, ymax, xmax])

                if not results:
                    continue

                results_point = Point(results.longitude, results.latitude)
                distance_improvement = fd.geom.centroid.distance(geom)-fd.geom.centroid.distance(results_point)

                if distance_improvement > 0:
                    print 'Moving geometry from: {geom.x}, {geom.y} to {results.longitude}, {results.latitude}.'.format(geom=geom, results=results)
                    print 'Distance improvement: {}'.format(distance_improvement)

                    if not options['dry_run']:
                        print update.format(results=results, where=where_clause)
                        cursor.execute(update.format(results=results, where=where_clause))

                    self.stdout.write('{} rows updated'.format(cursor.rowcount))
                else:
                    self.stdout.write('Not updating since {} is a negative distance improvement'.format(distance_improvement))

            except GeocoderQuotaExceeded:
                self.stdout.write('Geocoding Quota exceeded.')
                over_quota_exceptions += 1
                sleep(1)
                continue
            except GeocoderTimedOut:
                self.stdout.write('Geocoder Timed Out.')
                sleep(1)
                continue

            over_quota_exceptions = 0
            print '\n'

        cursor.execute('SET transform_null_equals TO OFF;')
    