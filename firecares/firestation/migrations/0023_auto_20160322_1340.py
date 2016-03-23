# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0022_firedepartment_twitter_handle'),
    ]

    operations = [
        migrations.RenameField(
            model_name='staffing',
            old_name='firefighter',
            new_name='personnel',
        ),
        migrations.RemoveField(
            model_name='staffing',
            name='chief_officer',
        ),
        migrations.RemoveField(
            model_name='staffing',
            name='ems_emt',
        ),
        migrations.RemoveField(
            model_name='staffing',
            name='ems_paramedic',
        ),
        migrations.RemoveField(
            model_name='staffing',
            name='ems_supervisor',
        ),
        migrations.RemoveField(
            model_name='staffing',
            name='firefighter_emt',
        ),
        migrations.RemoveField(
            model_name='staffing',
            name='firefighter_paramedic',
        ),
        migrations.RemoveField(
            model_name='staffing',
            name='officer',
        ),
        migrations.RemoveField(
            model_name='staffing',
            name='officer_paramedic',
        ),
        migrations.AddField(
            model_name='staffing',
            name='als',
            field=models.BooleanField(default=False),
        ),
    ]
