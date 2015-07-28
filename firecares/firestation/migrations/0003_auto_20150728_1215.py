# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0002_auto_20150728_1208'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='firedepartment',
            index_together=set([('population', 'id', 'region'), ('population', 'region')]),
        ),
    ]
