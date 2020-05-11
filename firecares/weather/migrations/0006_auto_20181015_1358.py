# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0005_auto_20181015_1355'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weatherwarnings',
            name='warnid',
            field=models.CharField(db_index=True, max_length=200, blank=True),
        ),
    ]
