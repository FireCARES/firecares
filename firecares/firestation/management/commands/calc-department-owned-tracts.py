from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from firecares.tasks.update import calculate_department_census_geom


class Command(BaseCommand):
    help = """Calculates and caches owned department boundaries based on census tracts that had a incidents responded to by the given department."""

    def add_arguments(self, parser):
        parser.add_argument('--ids', nargs='+', type=int, help='list of fire department ids to process')

    def handle(self, *args, **options):
        ids = options.get('ids')

        if ids is None:
            ids = FireDepartment.objects.all().values_list('id', flat=True)

        for i in ids:
            calculate_department_census_geom.delay(i)

        self.stdout.write(self.style.MIGRATE_SUCCESS('Queued {} departments for census tract updates'.format(len(ids))))
