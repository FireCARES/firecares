# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0051_auto_20170328_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='display_metrics',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='firedepartment',
            name='fdid',
            field=models.CharField(max_length=10, blank=True),
        ),
    ]
