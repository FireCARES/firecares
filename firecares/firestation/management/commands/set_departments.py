from firecares.firestation.models import FireStation
from django.db import transaction
from django.core.management.base import BaseCommand


def batch_qs(qs, batch_size=1000):
    """
    Returns a (start, end, total, queryset) tuple for each batch in the given
    queryset.
    """

    total = qs.count()
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        yield (start, end, total, qs[start:end])


class Command(BaseCommand):
    help = 'Sets departments for unmatched Fire Stations'
    queryset = None

    def add_arguments(self, parser):
        parser.add_argument('--state', '-s',
                            dest='state',
                            default=None,
                            help='State filter.')

        parser.add_argument('--batch', '-b',
                            dest='batch',
                            default=1,
                            help='Batch size.',
                            type=int)

        parser.add_argument('--limit', '-l',
                            dest='limit',
                            default=100,
                            help='Total number of records',
                            type=int)

    def handle(self, *args, **options):
        params = {'department__isnull': True}

        if options.get('state'):
            params['state'] = options.get('state')

        queryset = FireStation.objects.filter(**params)

        if options.get('limit'):
            queryset = queryset[:options.get('limit')]

        batches = batch_qs(queryset, options.get('batch'))

        for start, end, total, qs in batches:
            with transaction.atomic():
                to_commit = []

                for station in qs:

                    if not station.suggested_departments():
                        continue

                    print "Station:    {0}".format(station.name)
                    print "Department: {0}".format(station.suggested_departments()[0].name)
                    print "Dept Id   : {0}".format(station.suggested_departments()[0].id)
                    print

                    to_commit.append((station.id, station.suggested_departments()[0]))

                resp = raw_input('Look Ok? (y/n/q) ')

                if resp == 'y':
                    for id, dept in to_commit:
                        FireStation.objects.filter(id=id).update(department=dept)

                    print 'Committed'
                    print

                if resp == 'n':
                    continue

                if resp == 'q':
                    break
