import argparse
import pandas as pd
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment


class Command(BaseCommand):
    help = """Imports domain names from a csv roster file into FireCARES. The CSV file is expected
    to have the headers 'DepartmentID' and 'Email'"""

    def add_arguments(self, parser):
        parser.add_argument('file', help='source filename for a roster in CSV format', type=argparse.FileType('r'))
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do not execute update statements.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        csv = pd.read_csv(options['file'])

        cols = ['DepartmentID', 'Email']
        items = csv.groupby(cols)['DepartmentID', 'Email'].sum()
        for i, data in enumerate(items.iterrows()):
            fdid = data[0][0]
            domain = data[0][1].split('@')[1]
            self.stdout.write(str(fdid) + ' - ' + domain)

            fd = FireDepartment.objects.get(id=fdid)
            fd.domain_name = domain
            if not dry_run:
                fd.save()
        self.stdout.write('...done')
