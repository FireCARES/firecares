# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0060_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='staffing_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='firedepartment',
            name='stations_verified',
            field=models.BooleanField(default=False),
        ),
    ]
