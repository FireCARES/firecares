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

    def handle(self, *args, **options):
        department_ids = options.get('firedepartment_id') or FireDepartment.objects.filter(archived=False).values_list('id', flat=True)
        year = options.get('year') or None

        tasks = {}

        # launch async tasks for each department
        for department_id in department_ids:
            task = update_nfirs_counts.delay(department_id, year=year, stat=None)
            time.sleep(0.5)

            error = None

            while True:
                if task.ready():
                    try:
                        result = task.get()
                        print 'NFIRS update task complete: {}'.format(json.dumps({
                            'department_id': department_id,
                            'years': year,
                            }))
                    except Exception as e:
                        print 'NFIRS update task encountered an error: {} {}'.format(
                            json.dumps({
                                'department_id': department_id,
                                'years': year,
                            }), e)
                    finally:
                        break

                time.sleep(0.5)

        print 'Refreshing quartile and national calculations'
        refresh_quartile_task = refresh_quartile_view_task.delay()
        refresh_national_task = refresh_national_calculations_view_task.delay()

        refresh_quartile_task.get()
        refresh_national_task.get()
