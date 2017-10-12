# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentWarnings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('departmentfdid', models.CharField(max_length=10, blank=True)),
                ('departmentname', models.CharField(max_length=100)),
                ('warningfdid', models.CharField(max_length=100, blank=True)),
                ('warningname', models.CharField(max_length=200)),
                ('prod_type', models.CharField(max_length=100, null=True, blank=True)),
                ('expiredate', models.DateTimeField(null=True, blank=True)),
                ('issuedate', models.DateTimeField(null=True, blank=True)),
                ('url', models.CharField(max_length=500, null=True, blank=True)),
                ('warngeom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
        ),
        migrations.CreateModel(
            name='WeatherWarnings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('prod_type', models.CharField(max_length=200, null=True, blank=True)),
                ('oid', models.CharField(max_length=38, null=True, blank=True)),
                ('idp_source', models.CharField(max_length=200, null=True, blank=True)),
                ('idp_subset', models.CharField(max_length=200, null=True, blank=True)),
                ('url', models.CharField(max_length=500, null=True, blank=True)),
                ('event', models.CharField(max_length=200, null=True, blank=True)),
                ('wfo', models.CharField(max_length=200, null=True, blank=True)),
                ('warnid', models.CharField(max_length=200, blank=True)),
                ('phenom', models.CharField(max_length=200, null=True, blank=True)),
                ('sig', models.CharField(max_length=200, null=True, blank=True)),
                ('expiration', models.DateTimeField(null=True, blank=True)),
                ('idp_ingestdate', models.DateTimeField(null=True, blank=True)),
                ('issuance', models.DateTimeField(null=True, blank=True)),
                ('warngeom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
            options={
                'verbose_name': 'Weather Warnings',
            },
        ),
    ]
