import os
import argparse
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from firecares.tasks.update import update_parcel_department_effectivefirefighting_rollup

class Command(BaseCommand):
    help = """Updates the Effective Response Force (ERF) areas for the department"""

    def add_arguments(self, parser):
        parser.add_argument('--dept', nargs='*', help='Specify one or more department ids (omission will process all departments)')

    def handle(self, *args, **options):
        departments = options.get('dept')

        if not departments:
            departments = [value['id'] for value in FireDepartment.objects.values('id')]

        for department in departments:
            update_parcel_department_effectivefirefighting_rollup(department)
