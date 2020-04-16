# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0013_populationclass0quartile_populationclass1quartile_populationclass2quartile_populationclass3quartile_'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staffing',
            name='chief_officer',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'Chief Officer', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
    ]
