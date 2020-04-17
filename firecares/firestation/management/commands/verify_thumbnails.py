import requests
import sys
from firecares.firestation.models import FireDepartment
from django.core.management.base import BaseCommand
from optparse import make_option


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


class Command(BaseCommand):
    help = 'Verifies that the thumbnails for given department(s) are retrievable'
    args = '[department]'
    option_list = BaseCommand.option_list + (
        make_option('-d', '--department',
                    dest='department',
                    help='The FireCARES department id.'),
    )

    def handle(self, *args, **options):
        department_id = options.get('department')
        firedepartments = FireDepartment.objects.filter(pk=department_id) if department_id else FireDepartment.objects.all()
        fd_count = len(firedepartments)
        bad_thumbs = 0

        print('Looking up thumbnails for {cnt}'.format(cnt=fd_count))

        session = requests.Session()

        for idx, fd in enumerate(firedepartments):
            if not idx % 10:
                print('Processing ({idx}/{all})'.format(idx=idx, all=len(firedepartments)))
                sys.stdout.flush()

            resp = session.head(fd.thumbnail)
            if resp.status_code != 200:
                bad_thumbs += 1
                print('Bad thumbnail {url} for firepartment id: {id}'.format(id=fd.id, url=fd.thumbnail))

        if not firedepartments:
            print('Firedepartment(s) not found')
        else:
            print('# of bad fire department thumbnails => ({bad}/{all})'.format(bad=bad_thumbs, all=fd_count))
