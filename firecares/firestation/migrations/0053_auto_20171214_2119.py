# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0052_auto_20170731_1345'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='boundary_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='firedepartment',
            name='cfai_accredited',
            field=models.BooleanField(default=False),
        ),
    ]
