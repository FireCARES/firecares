# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0044_firedepartmentriskmodels_structure_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartmentriskmodels',
            name='floor_count_coefficients',
            field=annoying.fields.JSONField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='firedepartmentriskmodels',
            name='level',
            field=models.IntegerField(default=1, choices=[(0, b'All'), (4, b'High'), (1, b'Low'), (2, b'Medium'), (5, b'Unknown')]),
        ),
        migrations.AlterField(
            model_name='nfirsstatistic',
            name='level',
            field=models.IntegerField(default=1, db_index=True, choices=[(0, b'All'), (4, b'High'), (1, b'Low'), (2, b'Medium'), (5, b'Unknown')]),
        ),
    ]
