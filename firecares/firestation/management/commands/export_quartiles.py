import djqscsv
from django.core.management.base import BaseCommand
from firecares.firestation.models import FireDepartment


class Command(BaseCommand):
    help = 'Updates the DIST score for a department'
    option_list = BaseCommand.option_list + (
    )

    def handle(self, *args, **options):
        for clazz in range(0, 10):
            djqscsv.write_csv(FireDepartment.objects.filter(population_class=clazz).as_quartiles().values('id', 'fdid', 'state', 'name','dist_model_score', 'dist_model_score_quartile', 'population', 'population_class', 'risk_model_deaths', 'risk_model_deaths_quartile', 'risk_model_injuries', 'risk_model_injuries_quartile', 'risk_model_fires', 'risk_model_fires_quartile', 'risk_model_fires_size0', 'risk_model_fires_size0_quartile', 'risk_model_fires_size1', 'risk_model_fires_size1_quartile', 'risk_model_fires_size2', 'risk_model_fires_size2_quartile'), open('/tmp/population_class_{0}.csv'.format(clazz), 'wb'), use_verbose_names=False, field_header_map={'risk_model_fires_size0': 'risk_model_fires_size1', 'risk_model_fires_size1':'risk_model_fires_size2', 'risk_model_fires_size2':'risk_model_fires_size3'})

        # by region
        for region in ['West', 'South', 'Midwest', 'Northeast']:
            djqscsv.write_csv(FireDepartment.objects.filter(population_class__lte=8, region=region).as_quartiles().values('id', 'fdid', 'state', 'name','dist_model_score', 'dist_model_score_quartile', 'population', 'population_class', 'risk_model_deaths', 'risk_model_deaths_quartile', 'risk_model_injuries', 'risk_model_injuries_quartile', 'risk_model_fires', 'risk_model_fires_quartile', 'risk_model_fires_size0', 'risk_model_fires_size0_quartile', 'risk_model_fires_size1', 'risk_model_fires_size1_quartile', 'risk_model_fires_size2', 'risk_model_fires_size2_quartile'), open('/tmp/non_metropolitan_{0}.csv'.format(region), 'wb'), use_verbose_names=False, field_header_map={'risk_model_fires_size0': 'risk_model_fires_size1', 'risk_model_fires_size1':'risk_model_fires_size2', 'risk_model_fires_size2':'risk_model_fires_size3'})

        for region in ['West', 'South', 'Midwest', 'Northeast']:
            for clazz in range(0, 9):
                djqscsv.write_csv(FireDepartment.objects.filter(population_class=clazz, region=region).as_quartiles().values('id', 'fdid', 'state', 'name','dist_model_score', 'dist_model_score_quartile', 'population', 'population_class', 'risk_model_deaths', 'risk_model_deaths_quartile', 'risk_model_injuries', 'risk_model_injuries_quartile', 'risk_model_fires', 'risk_model_fires_quartile', 'risk_model_fires_size0', 'risk_model_fires_size0_quartile', 'risk_model_fires_size1', 'risk_model_fires_size1_quartile', 'risk_model_fires_size2', 'risk_model_fires_size2_quartile'), open('/tmp/{0}_population_class_{1}.csv'.format(region, clazz), 'wb'), use_verbose_names=False, field_header_map={'risk_model_fires_size0': 'risk_model_fires_size1', 'risk_model_fires_size1':'risk_model_fires_size2', 'risk_model_fires_size2':'risk_model_fires_size3'})

        djqscsv.write_csv(FireDepartment.objects.filter(population_class__in=[7, 8], region='Northeast').as_quartiles().values('id', 'fdid', 'state', 'name','dist_model_score', 'dist_model_score_quartile', 'population', 'population_class', 'risk_model_deaths', 'risk_model_deaths_quartile', 'risk_model_injuries', 'risk_model_injuries_quartile', 'risk_model_fires', 'risk_model_fires_quartile', 'risk_model_fires_size0', 'risk_model_fires_size0_quartile', 'risk_model_fires_size1', 'risk_model_fires_size1_quartile', 'risk_model_fires_size2', 'risk_model_fires_size2_quartile'), open('/tmp/{0}_population_class_7_8.csv'.format('Northeast', clazz), 'wb'), use_verbose_names=False, field_header_map={'risk_model_fires_size0': 'risk_model_fires_size1', 'risk_model_fires_size1':'risk_model_fires_size2', 'risk_model_fires_size2':'risk_model_fires_size3'})
