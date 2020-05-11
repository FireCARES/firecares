# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0043_auto_20170131_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartmentriskmodels',
            name='structure_count',
            field=models.IntegerField(null=True, verbose_name=b"Structure counts for this hazard level over department's owned census tracts", blank=True),
        ),
    ]
