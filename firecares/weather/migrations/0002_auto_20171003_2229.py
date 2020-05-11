# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='departmentwarnings',
            name='departmentfdid'
        ),
        migrations.AddField(
            model_name='departmentwarnings',
            name='departmentfdid',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='firestation.FireDepartment', null=True),
        ),
        migrations.RemoveField(
            model_name='departmentwarnings',
            name='warningfdid'
        ),
        migrations.AddField(
            model_name='departmentwarnings',
            name='warningfdid',
            field=models.ForeignKey(blank=True, to='weather.WeatherWarnings', null=True),
        ),
        migrations.AlterModelOptions(
            name='departmentwarnings',
            options={'ordering': ['milestone', 'sequence'], 'verbose_name_plural': 'processes'},
        ),
    ]
