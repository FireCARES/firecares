from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from firecares.tasks.update import calculate_story_distribution


class Command(BaseCommand):
    help = """Calculates the story distribution for a specific fire department, including similar departments """

    def add_arguments(self, parser):
        parser.add_argument('--ids', nargs='+', type=int, help='list of fire department ids to process')

    def handle(self, *args, **options):
        ids = options.get('ids')

        if ids is None:
            ids = FireDepartment.objects.all().values_list('id', flat=True)

        for i in ids:
            calculate_story_distribution.delay(i)

        self.stdout.write(self.style.MIGRATE_SUCCESS('Queued {} departments for story distribution calculations'.format(len(ids))))
