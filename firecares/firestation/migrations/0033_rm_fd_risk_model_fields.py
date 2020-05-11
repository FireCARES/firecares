# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0032_migrate_to_fd_risk_models'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='firedepartment',
            name='dist_model_score',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_deaths',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_size0',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_size0_percentage',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_size1',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_size1_percentage',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_size2',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_fires_size2_percentage',
        ),
        migrations.RemoveField(
            model_name='firedepartment',
            name='risk_model_injuries',
        ),
        migrations.AddField(
            model_name='nfirsstatistic',
            name='level',
            field=models.IntegerField(default=1, choices=[(1, b'Low'), (2, b'Medium'), (4, b'High')]),
        ),
    ]
