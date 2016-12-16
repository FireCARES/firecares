# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import phonenumber_field.modelfields
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0035_auto_20161219_1536'),
    ]

    operations = [
        migrations.CreateModel(
            name='PopulationClassQuartile',
            fields=[
                ('id', models.OneToOneField(primary_key=True, db_column=b'id', serialize=False, to='firestation.FireDepartment')),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField(editable=False)),
                ('fdid', models.CharField(max_length=10, editable=False)),
                ('name', models.CharField(max_length=100, editable=False)),
                ('headquarters_phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True, editable=False, blank=True)),
                ('headquarters_fax', phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True, editable=False, blank=True)),
                ('department_type', models.CharField(max_length=20, null=True, editable=False, blank=True)),
                ('organization_type', models.CharField(max_length=75, null=True, editable=False, blank=True)),
                ('website', models.URLField(null=True, editable=False, blank=True)),
                ('state', models.CharField(max_length=2, editable=False)),
                ('region', models.CharField(max_length=20, null=True, editable=False, blank=True)),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, editable=False, blank=True)),
                ('level', models.IntegerField(default=1, choices=[(1, b'Low'), (2, b'Medium'), (4, b'High')])),
                ('dist_model_score', models.FloatField(null=True, editable=False, blank=True)),
                ('risk_model_deaths', models.FloatField(verbose_name=b'Predicted deaths per year.', null=True, editable=False, blank=True)),
                ('risk_model_injuries', models.FloatField(verbose_name=b'Predicted injuries per year.', null=True, editable=False, blank=True)),
                ('risk_model_fires', models.FloatField(verbose_name=b'Predicted number of fires per year.', null=True, editable=False, blank=True)),
                ('risk_model_fires_size0', models.FloatField(verbose_name=b'Predicted number of size 0 fires.', null=True, editable=False, blank=True)),
                ('risk_model_fires_size0_percentage', models.FloatField(verbose_name=b'Percentage of size 0 fires.', null=True, editable=False, blank=True)),
                ('risk_model_fires_size1', models.FloatField(verbose_name=b'Predicted number of size 1 fires.', null=True, editable=False, blank=True)),
                ('risk_model_fires_size1_percentage', models.FloatField(verbose_name=b'Percentage of size 1 fires.', null=True, editable=False, blank=True)),
                ('risk_model_fires_size2', models.FloatField(verbose_name=b'Predicted number of size 2 firese.', null=True, editable=False, blank=True)),
                ('risk_model_fires_size2_percentage', models.FloatField(verbose_name=b'Percentage of size 2 fires.', null=True, editable=False, blank=True)),
                ('population', models.IntegerField(null=True, editable=False, blank=True)),
                ('population_class', models.IntegerField(null=True, editable=False, blank=True)),
                ('featured', models.BooleanField(default=False, editable=False)),
                ('dist_model_score_quartile', models.IntegerField()),
                ('risk_model_deaths_quartile', models.IntegerField()),
                ('risk_model_injuries_quartile', models.IntegerField()),
                ('risk_model_fires_size0_quartile', models.IntegerField()),
                ('risk_model_fires_size1_quartile', models.IntegerField()),
                ('risk_model_fires_size2_quartile', models.IntegerField()),
                ('risk_model_fires_quartile', models.IntegerField()),
                ('risk_model_size1_percent_size2_percent_sum_quartile', models.IntegerField()),
                ('risk_model_size1_percent_size2_percent_sum', models.FloatField(null=True, blank=True)),
                ('risk_model_deaths_injuries_sum', models.FloatField(null=True, blank=True)),
                ('risk_model_deaths_injuries_sum_quartile', models.IntegerField(null=True, blank=True)),
                ('residential_fires_avg_3_years', models.FloatField(null=True, blank=True)),
                ('residential_fires_avg_3_years_quartile', models.FloatField(null=True, blank=True)),
            ],
            options={
                'db_table': 'population_quartiles',
                'managed': False,
            },
        ),
    ]
