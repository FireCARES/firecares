# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0010_auto_20150812_1225'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_floor',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_floor_percentage',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_room',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_structure',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_structure_percentage',
        ),
    ]
