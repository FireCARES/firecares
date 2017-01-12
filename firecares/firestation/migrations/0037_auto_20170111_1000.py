# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0036_populationclassquartile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='firedepartmentriskmodels',
            name='level',
            field=models.IntegerField(default=1, choices=[(0, b'All'), (1, b'Low'), (2, b'Medium'), (4, b'High')]),
        ),
        migrations.AlterField(
            model_name='nfirsstatistic',
            name='level',
            field=models.IntegerField(default=1, db_index=True, choices=[(0, b'All'), (1, b'Low'), (2, b'Medium'), (4, b'High')]),
        ),
    ]
