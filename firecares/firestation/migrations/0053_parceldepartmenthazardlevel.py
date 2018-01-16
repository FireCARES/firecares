# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0052_auto_20170731_1345'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParcelDepartmentHazardLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('parcelcount_low_0_4', models.IntegerField(null=True, blank=True)),
                ('parcelcount_low_4_6', models.IntegerField(null=True, blank=True)),
                ('parcelcount_low_6_8', models.IntegerField(null=True, blank=True)),
                ('parcelcount_medium_0_4', models.IntegerField(null=True, blank=True)),
                ('parcelcount_medium_4_6', models.IntegerField(null=True, blank=True)),
                ('parcelcount_medium_6_8', models.IntegerField(null=True, blank=True)),
                ('parcelcount_high_0_4', models.IntegerField(null=True, blank=True)),
                ('parcelcount_high_4_6', models.IntegerField(null=True, blank=True)),
                ('parcelcount_high_6_8', models.IntegerField(null=True, blank=True)),
                ('parcelcount_unknown_0_4', models.IntegerField(null=True, blank=True)),
                ('parcelcount_unknown_4_6', models.IntegerField(null=True, blank=True)),
                ('parcelcount_unknown_6_8', models.IntegerField(null=True, blank=True)),
                ('drivetimegeom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('department', models.ForeignKey(blank=True, to='firestation.FireDepartment', null=True)),
            ],
        ),
    ]
