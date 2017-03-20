# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0048_nationalcalculations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='firedepartment',
            name='population_class',
            field=models.IntegerField(blank=True, null=True, db_index=True, choices=[(0, b'Population less than 2,500.'), (1, b'Population between 2,500 and 4,999.'), (2, b'Population between 5,000 and 9,999.'), (3, b'Population between 10,000 and 24,999.'), (4, b'Population between 25,000 and 49,999.'), (5, b'Population between 50,000 and 99,999.'), (6, b'Population between 100,000 and 249,999.'), (7, b'Population between 250,000 and 499,999.'), (8, b'Population between 500,000 and 999,999.'), (9, b'Population greater than 1,000,000.')]),
        ),
        migrations.AlterField(
            model_name='firedepartment',
            name='region',
            field=models.CharField(blank=True, max_length=20, null=True, db_index=True, choices=[(b'Northeast', b'Northeast'), (b'West', b'West'), (b'South', b'South'), (b'Midwest', b'Midwest'), (None, b'')]),
        ),
        migrations.AlterField(
            model_name='firedepartment',
            name='state',
            field=models.CharField(max_length=2, db_index=True),
        ),
    ]
