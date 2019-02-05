# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0004_auto_20171023_1719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentwarnings',
            name='warningname',
            field=models.CharField(max_length=200, db_index=True),
        ),
    ]
