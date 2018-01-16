# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0055_effectivefirefightingforcelevel'),
    ]

    operations = [
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='drivetimegeom_38_plus',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
    ]
