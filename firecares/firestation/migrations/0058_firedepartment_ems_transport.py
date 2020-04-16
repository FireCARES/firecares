# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0057_auto_20171214_2031'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='ems_transport',
            field=models.BooleanField(default=True),
        ),
    ]
