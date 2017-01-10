import argparse
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """Imports fire chief department associations into FireCARES.  Expects incoming CSV data to have columns including:
Department, Email
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
        pass
