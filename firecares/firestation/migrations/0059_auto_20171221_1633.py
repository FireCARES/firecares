# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0058_firedepartment_ems_transport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='firedepartment',
            name='ems_transport',
            field=models.BooleanField(default=False),
        ),
    ]
