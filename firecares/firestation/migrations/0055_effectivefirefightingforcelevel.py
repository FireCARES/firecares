# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0054_auto_20171102_1242'),
    ]

    operations = [
        migrations.CreateModel(
            name='EffectiveFireFightingForceLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('parcelcount_low_15_26', models.IntegerField(null=True, blank=True)),
                ('parcelcount_medium_27_42', models.IntegerField(null=True, blank=True)),
                ('parcelcount_high_43_plus', models.IntegerField(null=True, blank=True)),
                ('parcelcount_unknown_15_26', models.IntegerField(null=True, blank=True)),
                ('drivetimegeom_014', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('drivetimegeom_15_26', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('drivetimegeom_27_42', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('drivetimegeom_43_plus', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('department', models.ForeignKey(blank=True, to='firestation.FireDepartment', null=True)),
            ],
        ),
    ]
