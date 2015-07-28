# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='firedepartment',
            options={'ordering': ('name',)},
        ),
        migrations.AlterIndexTogether(
            name='firedepartment',
            index_together=set([('population', 'id', 'region')]),
        ),
    ]
