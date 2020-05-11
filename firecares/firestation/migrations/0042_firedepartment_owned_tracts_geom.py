# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0041_auto_20170127_2136'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='owned_tracts_geom',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
    ]
