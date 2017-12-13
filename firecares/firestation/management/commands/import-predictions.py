import argparse
import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment
from firecares.tasks.update import (
    update_performance_score, refresh_quartile_view_task, refresh_national_calculations_view_task)
from firecares.utils import lenient_summation


class Command(BaseCommand):
    help = """Imports prediction data into FireCARES.  Expects incoming CSV data to have columns including:
fd_id, lr.fire, mr.fire, hr.fires, lr.injuries, mr.injuries, hr.injuries, lr.deaths.1se, mr.deaths, hr.deaths, lr.sz2, mr.sz2, hr.sz2, lr.sz3, mr.sz3, hr.sz3
    """

    def add_arguments(self, parser):
        parser.add_argument('file', help='source filename for predictions in CSV format', type=argparse.FileType('r'))
        parser.add_argument('--ids', nargs='+', type=int, help='list of fire department ids to process from the CSV (defaults to all departments)')

        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do not execute update statements.',
        )

    def calculate_derived_values(self, obj):
        # Derived values update...
        if obj.risk_model_fires:
            obj.risk_model_fires_size0_percentage = None
            obj.risk_model_fires_size1_percentage = (obj.risk_model_fires_size1 or 0) / obj.risk_model_fires
            obj.risk_model_fires_size2_percentage = (obj.risk_model_fires_size2 or 0) / obj.risk_model_fires

    def handle(self, *args, **options):
        ids = options.get('ids')
        dry_run = options.get('dry_run')
        df = pd.read_csv(options['file'])
        count = 0
        cols = ['fd_id', 'lr.fire', 'mr.fire', 'hr.fires', 'lr.injuries', 'mr.injuries', 'hr.injuries',
                'lr.deaths.1se', 'mr.deaths', 'hr.deaths',
                'lr.sz2', 'mr.sz2', 'hr.sz2', 'lr.sz3', 'mr.sz3', 'hr.sz3',
                'lr_beyond_room', 'lr_beyond_structure',
                'mr_beyond_room', 'mr_beyond_structure',
                'hr_beyond_room', 'hr_beyond_structure']

        df['lr_beyond_room'] = df.apply(lambda row: row['lr.fire'] * row['lr.sz2'], axis=1)
        df['lr_beyond_structure'] = df.apply(lambda row: row['lr.fire'] * row['lr.sz2'] * row['lr.sz3'], axis=1)
        df['mr_beyond_room'] = df.apply(lambda row: row['mr.fire'] * row['mr.sz2'], axis=1)
        df['mr_beyond_structure'] = df.apply(lambda row: row['mr.fire'] * row['mr.sz2'] * row['mr.sz3'], axis=1)
        df['hr_beyond_room'] = df.apply(lambda row: row['hr.fires'] * row['hr.sz2'], axis=1)
        df['hr_beyond_structure'] = df.apply(lambda row: row['hr.fires'] * row['hr.sz2'] * row['hr.sz3'], axis=1)

        items = df[cols]

        def valid(num):
            return not np.isnan(num) and num != 0

        for idx, i in enumerate(items.iterrows()):
            cur_id = int(i[1]['fd_id'])
            row = i[1]

            if ids is None or cur_id in ids:

                row = df[df.fd_id == cur_id].to_dict(orient='row')[0]

                lr_beyond_room = row['lr_beyond_room']
                lr_beyond_structure = row['lr_beyond_structure']
                mr_beyond_room = row['mr_beyond_room']
                mr_beyond_structure = row['mr_beyond_structure']
                hr_beyond_room = row['hr_beyond_room']
                hr_beyond_structure = row['hr_beyond_structure']

                fd = FireDepartment.objects.filter(id=cur_id).first()
                if fd is None:
                    continue

                low, _ = fd.firedepartmentriskmodels_set.get_or_create(level=1)
                medium, _ = fd.firedepartmentriskmodels_set.get_or_create(level=2)
                high, _ = fd.firedepartmentriskmodels_set.get_or_create(level=4)
                unknown, _ = fd.firedepartmentriskmodels_set.get_or_create(level=5)
                all_level, _ = fd.firedepartmentriskmodels_set.get_or_create(level=0)

                self.stdout.write('Updating predictions for {} ({} of {})'.format(fd, idx + 1, len(items)), ending='')

                low.risk_model_deaths = row['lr.deaths.1se'] if valid(row['lr.deaths.1se']) else low.risk_model_deaths
                low.risk_model_injuries = row['lr.injuries'] if valid(row['lr.injuries']) else low.risk_model_injuries
                low.risk_model_fires = row['lr.fire'] if valid(row['lr.fire']) else low.risk_model_fires
                low.risk_model_fires_size0 = None
                low.risk_model_fires_size1 = lr_beyond_room if valid(lr_beyond_room) else low.risk_model_fires_size1
                low.risk_model_fires_size2 = lr_beyond_structure if valid(lr_beyond_structure) else low.risk_model_fires_size2
                self.calculate_derived_values(low)

                medium.risk_model_deaths = row['mr.deaths'] if valid(row['mr.deaths']) else medium.risk_model_deaths
                medium.risk_model_injuries = row['mr.injuries'] if valid(row['mr.injuries']) else medium.risk_model_injuries
                medium.risk_model_fires = row['mr.fire'] if valid(row['mr.fire']) else medium.risk_model_fires
                medium.risk_model_fires_size0 = None
                medium.risk_model_fires_size1 = mr_beyond_room if valid(mr_beyond_room) else medium.risk_model_fires_size1
                medium.risk_model_fires_size2 = mr_beyond_structure if valid(mr_beyond_structure) else medium.risk_model_fires_size2
                self.calculate_derived_values(medium)

                high.risk_model_deaths = row['hr.deaths'] if valid(row['hr.deaths']) else high.risk_model_deaths
                high.risk_model_injuries = row['hr.injuries'] if valid(row['hr.injuries']) else high.risk_model_injuries
                high.risk_model_fires = row['hr.fires'] if valid(row['hr.fires']) else high.risk_model_fires
                high.risk_model_fires_size0 = None
                high.risk_model_fires_size1 = hr_beyond_room if valid(hr_beyond_room) else high.risk_model_fires_size1
                high.risk_model_fires_size2 = hr_beyond_structure if valid(hr_beyond_structure) else high.risk_model_fires_size2
                self.calculate_derived_values(high)

                all_level.risk_model_deaths = lenient_summation(low.risk_model_deaths, medium.risk_model_deaths, high.risk_model_deaths)
                all_level.risk_model_injuries = lenient_summation(low.risk_model_injuries, medium.risk_model_injuries, high.risk_model_injuries)
                all_level.risk_model_fires = lenient_summation(low.risk_model_fires, medium.risk_model_fires, high.risk_model_fires)
                all_level.risk_model_fires_size0 = None
                all_level.risk_model_fires_size1 = lenient_summation(low.risk_model_fires_size1, medium.risk_model_fires_size1, high.risk_model_fires_size1)
                all_level.risk_model_fires_size2 = lenient_summation(low.risk_model_fires_size2, medium.risk_model_fires_size2, high.risk_model_fires_size2)
                self.calculate_derived_values(all_level)

                # No data for "unknown" risk level in terms of predictions...

                if not dry_run:
                    count = count + 1
                    low.save()
                    medium.save()
                    high.save()
                    all_level.save()
                    update_performance_score.delay(fd.id)

                self.stdout.write('...done')

        self.stdout.write(self.style.MIGRATE_SUCCESS('Updated/created prediction records for {} departments'.format(count)))

        if not dry_run:
            self.stdout.write('Creating/refreshing "population_quartiles" view')
            refresh_quartile_view_task.delay()
            self.stdout.write('Creating/refreshing "national_calculations" view')
            refresh_national_calculations_view_task.delay()
