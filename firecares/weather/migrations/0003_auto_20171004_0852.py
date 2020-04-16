# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0052_auto_20170731_1345'),
        ('weather', '0002_auto_20171003_2229'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='departmentwarnings',
            options={},
        ),
        migrations.AddField(
            model_name='departmentwarnings',
            name='department',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='firestation.FireDepartment', null=True),
        ),
        migrations.AlterField(
            model_name='departmentwarnings',
            name='departmentfdid',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
    ]
