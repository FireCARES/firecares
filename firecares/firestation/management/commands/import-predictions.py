import argparse
import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment, FireDepartmentRiskModels
from firecares.tasks.update import update_performance_score, create_quartile_views_task
from firecares.utils import lenient_summation, lenient_mean


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
        obj.risk_model_fires = lenient_summation(obj.risk_model_fires_size0, obj.risk_model_fires_size1, obj.risk_model_fires_size2)
        if obj.risk_model_fires:
            obj.risk_model_fires_size0_percentage = (obj.risk_model_fires_size0 or 0) / obj.risk_model_fires
            obj.risk_model_fires_size1_percentage = (obj.risk_model_fires_size1 or 0) / obj.risk_model_fires
            obj.risk_model_fires_size2_percentage = (obj.risk_model_fires_size2 or 0) / obj.risk_model_fires

    def handle(self, *args, **options):
        ids = options.get('ids')
        dry_run = options.get('dry_run')
        df = pd.read_csv(options['file'])
        count = 0
        cols = ['lr_fire', 'mr_fire', 'h.fire', 'lr_inj', 'mr_inj', 'h.inj', 'lr_death', 'mr_death', 'h.death', 'lr_size_2', 'mr_size_2', 'h.size2', 'lr_size_3', 'mr_size_3', 'h.size3']
        items = df.groupby(['fd_id', 'state'])[cols].sum()
        # Assumption: Mapping *_size_2 to risk_model_fires_size1 and *_size_3 to risk_model_fires_size2
        # Another assumption: if the incoming value is NaN, then DON'T update an existing valid value

        def valid(num):
            return not np.isnan(num)

        for idx, i in enumerate(items.iterrows()):
            cur_id = int(i[0][0])
            row = i[1]
            if ids is None or cur_id in ids:
                fd = FireDepartment.objects.filter(id=cur_id).first()
                low = fd.firedepartmentriskmodels_set.filter(level=1).first() or FireDepartmentRiskModels(department=fd, level=1)
                medium = fd.firedepartmentriskmodels_set.filter(level=2).first() or FireDepartmentRiskModels(department=fd, level=2)
                high = fd.firedepartmentriskmodels_set.filter(level=4).first() or FireDepartmentRiskModels(department=fd, level=4)
                all_level = fd.firedepartmentriskmodels_set.filter(level=0).first() or FireDepartmentRiskModels(department=fd, level=0)

                self.stdout.write('Updating risk models for {} ({} of {})'.format(fd, idx + 1, len(items)), ending='')

                low.risk_model_deaths = row['lr_death'] if valid(row['lr_death']) else low.risk_model_deaths
                low.risk_model_injuries = row['lr_inj'] if valid(row['lr_inj']) else low.risk_model_injuries
                low.risk_model_fires_size0 = row['lr_fire'] if valid(row['lr_fire']) else low.risk_model_fires_size0
                low.risk_model_fires_size1 = row['lr_size_2'] if valid(row['lr_size_2']) else low.risk_model_fires_size1
                low.risk_model_fires_size2 = row['lr_size_3'] if valid(row['lr_size_3']) else low.risk_model_fires_size2
                self.calculate_derived_values(low)

                medium.risk_model_deaths = row['mr_death'] if valid(row['mr_death']) else medium.risk_model_deaths
                medium.risk_model_injuries = row['mr_inj'] if valid(row['mr_inj']) else medium.risk_model_injuries
                medium.risk_model_fires_size0 = row['mr_fire'] if valid(row['mr_fire']) else medium.risk_model_fires_size0
                medium.risk_model_fires_size1 = row['mr_size_2'] if valid(row['mr_size_2']) else medium.risk_model_fires_size1
                medium.risk_model_fires_size2 = row['mr_size_3'] if valid(row['mr_size_3']) else medium.risk_model_fires_size2
                self.calculate_derived_values(medium)

                high.risk_model_deaths = row['h.death'] if valid(row['h.death']) else high.risk_model_deaths
                high.risk_model_injuries = row['h.inj'] if valid(row['h.inj']) else high.risk_model_injuries
                high.risk_model_fires_size0 = row['h.fire'] if valid(row['h.fire']) else high.risk_model_fires_size0
                high.risk_model_fires_size1 = row['h.size2'] if valid(row['h.size2']) else high.risk_model_fires_size1
                high.risk_model_fires_size2 = row['h.size3'] if valid(row['h.size3']) else high.risk_model_fires_size2
                self.calculate_derived_values(high)

                all_level.dist_model_score = lenient_mean(low.dist_model_score, medium.dist_model_score, high.dist_model_score)
                all_level.risk_model_deaths = lenient_summation(low.risk_model_deaths, medium.risk_model_deaths, high.risk_model_deaths)
                all_level.risk_model_injuries = lenient_summation(low.risk_model_injuries, medium.risk_model_injuries, high.risk_model_injuries)
                all_level.risk_model_fires_size0 = lenient_summation(low.risk_model_fires_size0, medium.risk_model_fires_size0, high.risk_model_fires_size0)
                all_level.risk_model_fires_size1 = lenient_summation(low.risk_model_fires_size1, medium.risk_model_fires_size1, high.risk_model_fires_size1)
                all_level.risk_model_fires_size2 = lenient_summation(low.risk_model_fires_size2, medium.risk_model_fires_size2, high.risk_model_fires_size2)
                self.calculate_derived_values(all_level)

                # TODO: Add nifrsstatistic "all" level calculations

                if not dry_run:
                    count = count + 1
                    low.save()
                    medium.save()
                    high.save()
                    all_level.save()
                    update_performance_score.delay(fd.id)

                self.stdout.write('...done')

        self.stdout.write(self.style.MIGRATE_SUCCESS('Updated/created risk model records for {} departments'.format(count)))
        if not dry_run:
            self.stdout.write('Creating/refreshing "population_quartiles" view')
            create_quartile_views_task.delay()
