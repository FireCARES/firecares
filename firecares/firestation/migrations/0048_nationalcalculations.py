# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0047_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='NationalCalculations',
            fields=[
                ('id', models.OneToOneField(primary_key=True, db_column=b'id', serialize=False, to='firestation.FireDepartment')),
                ('level', models.IntegerField(default=1, choices=[(0, b'All'), (4, b'High'), (1, b'Low'), (2, b'Medium'), (5, b'Unknown')])),
                ('risk_model_size1_percent_size2_percent_sum_quartile', models.IntegerField(null=True, blank=True)),
                ('risk_model_deaths_injuries_sum_quartile', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'national_calculations',
                'managed': False,
            },
        ),
    ]
