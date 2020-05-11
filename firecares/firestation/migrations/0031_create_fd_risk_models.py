# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0030_auto_20161123_1349'),
    ]

    operations = [
        migrations.CreateModel(
            name='FireDepartmentRiskModels',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('level', models.IntegerField(default=1, choices=[(1, b'Low'), (2, b'Medium'), (4, b'High')])),
                ('dist_model_score', models.FloatField(db_index=True, null=True, editable=False, blank=True)),
                ('risk_model_deaths', models.FloatField(db_index=True, null=True, verbose_name=b'Predicted deaths per year.', blank=True)),
                ('risk_model_injuries', models.FloatField(db_index=True, null=True, verbose_name=b'Predicted injuries per year.', blank=True)),
                ('risk_model_fires', models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of fires per year.', blank=True)),
                ('risk_model_fires_size0', models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of size 0 fires.', blank=True)),
                ('risk_model_fires_size0_percentage', models.FloatField(null=True, verbose_name=b'Percentage of size 0 fires.', blank=True)),
                ('risk_model_fires_size1', models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of size 1 fires.', blank=True)),
                ('risk_model_fires_size1_percentage', models.FloatField(null=True, verbose_name=b'Percentage of size 1 fires.', blank=True)),
                ('risk_model_fires_size2', models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of size 2 firese.', blank=True)),
                ('risk_model_fires_size2_percentage', models.FloatField(null=True, verbose_name=b'Percentage of size 2 fires.', blank=True)),
                ('department', models.ForeignKey(to='firestation.FireDepartment')),
            ],
        ),
    ]
