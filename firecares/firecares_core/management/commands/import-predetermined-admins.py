import argparse
import pandas as pd
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from firecares.firecares_core.models import PredeterminedUser


class Command(BaseCommand):
    help = """Imports users with pre-existing department associations into FireCARES, administrator is the default role assigned for associated department.  Expects incoming CSV data to have columns including:
Department, Address, Email, First Name, Last Name
    """

    def add_arguments(self, parser):
        parser.add_argument('file', help='source filename for chiefs in CSV format', type=argparse.FileType('r'))

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do not execute update statements.',
        )

    def handle(self, *args, **options):
        f = options['file']
        dry_run = options['dry_run']
        df = pd.read_csv(f)
        df = df[['DepartmentID', 'Email', 'First Name', 'Last Name']]
        for row in df.to_dict(orient='records'):
            fd = FireDepartment.objects.get(id=row['DepartmentID'])
            pu = PredeterminedUser.objects.filter(email=row['Email'], department=fd).first()
            if not pu:
                pu = PredeterminedUser(email=row['Email'], department=fd, first_name=row['First Name'], last_name=row['Last Name'])
                self.stdout.write('Creating {} to {} administrator association'.format(row['Email'], fd.name))
            else:
                self.stdout.write('Skipping import of {}...already exists'.format(row['Email']))

            if not dry_run:
                pu.save()
