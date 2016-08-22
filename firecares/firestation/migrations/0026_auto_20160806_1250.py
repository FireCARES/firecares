# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import firecares.firestation.models


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0025_auto_20160627_1506'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='firestation',
            name='archived',
            field=models.BooleanField(default=False),
        )
    ]
