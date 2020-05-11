# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0053_parceldepartmenthazardlevel'),
    ]

    operations = [
        migrations.RenameField(
            model_name='parceldepartmenthazardlevel',
            old_name='drivetimegeom',
            new_name='drivetimegeom_0_4',
        ),
        migrations.AddField(
            model_name='parceldepartmenthazardlevel',
            name='drivetimegeom_4_6',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='parceldepartmenthazardlevel',
            name='drivetimegeom_6_8',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
    ]
