# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0061_auto_20180202_2056'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='census_override',
            field=models.BooleanField(default=False),
        ),
    ]
