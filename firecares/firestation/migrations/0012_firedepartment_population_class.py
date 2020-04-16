# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0011_auto_20150812_1302'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='population_class',
            field=models.IntegerField(blank=True, null=True, choices=[(0, b'Population less than 2,500.'), (1, b'Population between 2,500 and 4,999.'), (2, b'Population between 5,000 and 9,999.'), (3, b'Population between 10,000 and 24,999.'), (4, b'Population between 25,000 and 49,999.'), (5, b'Population between 50,000 and 99,999.'), (6, b'Population between 100,000 and 249,999.'), (7, b'Population between 250,000 and 499,999.'), (8, b'Population between 500,000 and 999,999.'), (9, b'Population greater than 1,000,000.')]),
        ),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=0 where population<2500;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=1 where population>=2500 and population<=4999;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=2 where population>=5000 and population<=9999;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=3 where population>=10000 and population<=24999;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=4 where population>=25000 and population<=49999;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=5 where population>=50000 and population<=99999;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=6 where population>=100000 and population<=249999;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=7 where population>=250000 and population<=499999;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=8 where population>=500000 and population<=999999;"),
        migrations.RunSQL("UPDATE firestation_firedepartment set population_class=9 where population>=1000000;"),
    ]
