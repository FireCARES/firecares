# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0062_firedepartment_census_override'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='additional_fdids',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
