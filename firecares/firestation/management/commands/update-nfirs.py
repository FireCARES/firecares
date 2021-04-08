import pdb
import time
import json
from firecares.firestation.models import FireDepartment
from firecares.tasks.update import update_nfirs_counts, refresh_quartile_view_task, refresh_national_calculations_view_task
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Updates the NFIRS statistics for a department'

    def add_arguments(self, parser):
        parser.add_argument('firedepartment_id', nargs='*', type=int)
        parser.add_argument('--year', nargs='*', type=int, help='Year')
        parser.add_argument('--async', default=False, dest='async', action='store_true', help='Run update tasks asynchronously')

    def handle(self, *args, **options):
        department_ids = options.get('firedepartment_id') or FireDepartment.objects.filter(archived=False).values_list('id', flat=True)
        year = options.get('year') or None

        for department_id in department_ids:
            # launch async tasks for each department
            if options.get('async'):
                task = update_nfirs_counts.delay(department_id, year=year, stat=None)
                print 'NFIRS update task commenced: {}'.format(json.dumps({
                    'id': task.id,
                    'department_id': department_id,
                    'years': year,
                }))
            # run tasks synchronously
            else:
                update_nfirs_counts(department_id, year=year, stat=None)
                print 'NFIRS update task completed: {}'.format(json.dumps({
                    'department_id': department_id,
                    'years': year,
                }))
