from firecares.tasks.update import update_performance_score
from firecares.firestation.models import FireDepartment
from django.core.management.base import BaseCommand
from optparse import make_option


class Command(BaseCommand):
    help = 'Updates the DIST score for a department'
    option_list = BaseCommand.option_list + (
        make_option('-d', '--dry-run',
                    dest='dry_run',
                    default=False,
                    help='If specified the Fire Department records will not updated.'),
    )

    def handle(self, *args, **options):
        for fd in FireDepartment.objects.filter(archived=False):
            update_performance_score.delay(fd.id, options.get('dry_run'))
