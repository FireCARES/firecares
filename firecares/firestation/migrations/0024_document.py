# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import firecares.firestation.models


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0023_auto_20160322_1340'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('filename', models.CharField(max_length=260, null=True, blank=True)),
                ('file', models.FileField(storage=firecares.firestation.models.DocumentS3Storage(bucket=b'firecares-uploads'), upload_to=firecares.firestation.models.document_upload_to)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='firestation.FireDepartment', null=True)),
            ],
        ),
    ]
