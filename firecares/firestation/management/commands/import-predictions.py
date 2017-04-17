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
fd_id, state, lr_fire, mr_fire, h.fire, lr_inj, mr_inj, h.inj, lr_death, mr_death, h.death, lr_size_2, mr_size_2, h.size2, lr_size_3, mr_size_3, h.size3
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
        cols = ['lr_fire', 'mr_fire', 'h.fire', 'lr_inj', 'mr_inj', 'h.inj', 'lr_death', 'mr_death', 'h.death', 'lr_size_2', 'mr_size_2', 'h.size2', 'lr_size_3', 'mr_size_3', 'h.size3']

        items = df.groupby(['fd_id', 'state'])[cols].sum()

        def valid(num):
            return not np.isnan(num)

        for idx, i in enumerate(items.iterrows()):
            cur_id = int(i[0][0])
            row = i[1]
            if ids is None or cur_id in ids:
                df['lr_beyond_room'] = df[df['fd_id'] == cur_id].apply(lambda row: row['lr_fire'] * row['lr_size_2'], axis=1)
                df['lr_beyond_structure'] = df[df['fd_id'] == cur_id].apply(lambda row: row['lr_fire'] * row['lr_size_2'] * row['lr_size_3'], axis=1)
                df['mr_beyond_room'] = df[df['fd_id'] == cur_id].apply(lambda row: row['mr_fire'] * row['mr_size_2'], axis=1)
                df['mr_beyond_structure'] = df[df['fd_id'] == cur_id].apply(lambda row: row['mr_fire'] * row['mr_size_2'] * row['mr_size_3'], axis=1)
                df['hr_beyond_room'] = df[df['fd_id'] == cur_id].apply(lambda row: row['h.fire'] * row['h.size2'], axis=1)
                df['hr_beyond_structure'] = df[df['fd_id'] == cur_id].apply(lambda row: row['h.fire'] * row['h.size2'] * row['h.size3'], axis=1)

                sums = df[df['fd_id'] == cur_id].groupby(['fd_id', 'state']).sum()

                lr_beyond_room = sums['lr_beyond_room'][0]
                lr_beyond_structure = sums['lr_beyond_structure'][0]
                mr_beyond_room = sums['mr_beyond_room'][0]
                mr_beyond_structure = sums['mr_beyond_structure'][0]
                hr_beyond_room = sums['hr_beyond_room'][0]
                hr_beyond_structure = sums['hr_beyond_structure'][0]

                fd = FireDepartment.objects.filter(id=cur_id).first()
                low, _ = fd.firedepartmentriskmodels_set.get_or_create(level=1)
                medium, _ = fd.firedepartmentriskmodels_set.get_or_create(level=2)
                high, _ = fd.firedepartmentriskmodels_set.get_or_create(level=4)
                unknown, _ = fd.firedepartmentriskmodels_set.get_or_create(level=5)
                all_level, _ = fd.firedepartmentriskmodels_set.get_or_create(level=0)

                self.stdout.write('Updating predictions for {} ({} of {})'.format(fd, idx + 1, len(items)), ending='')

                low.risk_model_deaths = row['lr_death'] if valid(row['lr_death']) else low.risk_model_deaths
                low.risk_model_injuries = row['lr_inj'] if valid(row['lr_inj']) else low.risk_model_injuries
                low.risk_model_fires = row['lr_fire'] if valid(row['lr_fire']) else low.risk_model_fires
                low.risk_model_fires_size0 = None
                low.risk_model_fires_size1 = lr_beyond_room if valid(lr_beyond_room) else low.risk_model_fires_size1
                low.risk_model_fires_size2 = lr_beyond_structure if valid(lr_beyond_structure) else low.risk_model_fires_size2
                self.calculate_derived_values(low)

                medium.risk_model_deaths = row['mr_death'] if valid(row['mr_death']) else medium.risk_model_deaths
                medium.risk_model_injuries = row['mr_inj'] if valid(row['mr_inj']) else medium.risk_model_injuries
                medium.risk_model_fires = row['mr_fire'] if valid(row['mr_fire']) else medium.risk_model_fires
                medium.risk_model_fires_size0 = None
                medium.risk_model_fires_size1 = mr_beyond_room if valid(mr_beyond_room) else medium.risk_model_fires_size1
                medium.risk_model_fires_size2 = mr_beyond_structure if valid(mr_beyond_structure) else medium.risk_model_fires_size2
                self.calculate_derived_values(medium)

                high.risk_model_deaths = row['h.death'] if valid(row['h.death']) else high.risk_model_deaths
                high.risk_model_injuries = row['h.inj'] if valid(row['h.inj']) else high.risk_model_injuries
                high.risk_model_fires = row['h.fire'] if valid(row['h.fire']) else high.risk_model_fires
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

                # TODO: Add nifrsstatistic "all" level calculations

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
