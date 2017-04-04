import argparse
import pandas as pd
from firecares.firestation.models import FireDepartment
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """Updates IAFF local numbers using a given CSV. Expects incoming CSV data to have columns including:
firecares_id, fdid, State_Code, IAFF_local"""

    def add_arguments(self, parser):
        parser.add_argument('file', help='source filename for predictions in CSV format', type=argparse.FileType('r'))

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do not execute update statements.',
        )

    def handle(self, *args, **options):
        df = pd.read_csv(options['file']).dropna(axis='columns', how='all')
        dry_run = options.get('dry_run')

        groups = df[['fdid', 'State_Code', 'firecares_id', 'IAFF_local']].groupby(['fdid', 'State_Code'])
        keys = map(lambda x: x[0], groups)
        ret = []

        for k in keys:
            g = groups.get_group(name=k)
            fc_id = g[g['firecares_id'].notnull()]['firecares_id'].values

            if fc_id.any():
                print 'IMPORTING: {} with local numbers: {}'.format(fc_id[0], ','.join(map(str, g['IAFF_local'].values)))
                ret.append({'fc_id': fc_id[0], 'locals': ','.join(map(str, g['IAFF_local'].values))})
            else:
                rec = df.loc[g.index[0], :]
                print 'SKIPPING {},{}:\n{}'.format(rec['fdid'], rec['State_Code'], rec)

        if not dry_run:
            for r in ret:
                if not FireDepartment.objects.filter(id=r['fc_id']).update(iaff=r['locals']):
                    print 'MISSING Fire Department with FireCARES ID = {} for local # {}'.format(r['fc_id'], r['locals'])
