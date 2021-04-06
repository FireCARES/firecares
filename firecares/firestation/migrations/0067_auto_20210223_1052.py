# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import firecares.firestation.models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0066_staffing_other_apparatus_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='firestation',
            name='service_area_0_4',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='firestation',
            name='service_area_4_6',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='firestation',
            name='service_area_6_8',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(storage=firecares.firestation.models.DocumentS3Storage(bucket=b'firecares-uploads'), upload_to=firecares.firestation.models.document_upload_to),
        ),
    ]
