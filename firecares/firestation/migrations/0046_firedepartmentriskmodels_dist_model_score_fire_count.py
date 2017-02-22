# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0045_auto_20170206_1529'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartmentriskmodels',
            name='dist_model_score_fire_count',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
