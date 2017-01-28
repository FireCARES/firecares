# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0040_auto_20170126_1640'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='nfirsstatistic',
            unique_together=set([('fire_department', 'year', 'metric', 'level')]),
        ),
    ]
