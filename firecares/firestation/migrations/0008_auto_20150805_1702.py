# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0007_auto_20150802_2004'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_deaths',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted deaths per year.', blank=True),
        ),
        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_floor',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted fires confined to the floor of origin.', blank=True),
        ),
        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_room',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted fires confined to the room of origin.', blank=True),
        ),
        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_structure',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted fires beyond the structure of origin.', blank=True),
        ),
        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_injuries',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted injuries per year.', blank=True),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='chief_officer',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'Cheif Officer', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='ems_emt',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'EMS-Only EMT', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='ems_paramedic',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'EMS-Only Paramedic', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='ems_supervisor',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'EMS Supervisor', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='firefighter',
            field=models.PositiveIntegerField(default=0, null=True, blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='firefighter_emt',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'Firefighter EMT', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='firefighter_paramedic',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'Firefighter Paramedic', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='officer',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'Company/Unit Officer', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='staffing',
            name='officer_paramedic',
            field=models.PositiveIntegerField(default=0, null=True, verbose_name=b'Company/Unit Officer Paramedic', blank=True, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
    ]
