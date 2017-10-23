# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0003_auto_20171004_0852'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentwarnings',
            name='warngeom',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True),
        ),
        migrations.AlterField(
            model_name='weatherwarnings',
            name='warngeom',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True),
        ),
    ]
