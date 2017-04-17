# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0050_fix_invalid_riskmodels'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='firedepartmentriskmodels',
            unique_together=set([('level', 'department')]),
        ),
    ]
