# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0065_auto_20181012_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffing',
            name='other_apparatus_type',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
