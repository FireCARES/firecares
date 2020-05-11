from firecares.tasks.update import update_nfirs_counts
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Updates the NFIRS statistics for a department'

    def add_arguments(self, parser):
        parser.add_argument('firedepartment_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for department in options.get('firedepartment_id'):
            update_nfirs_counts.delay(department)
