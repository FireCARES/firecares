# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('address_line1', models.CharField(max_length=100, verbose_name=b'Address line 1')),
                ('address_line2', models.CharField(max_length=100, verbose_name=b'Address line 2', blank=True)),
                ('city', models.CharField(max_length=50)),
                ('state_province', models.CharField(max_length=40, verbose_name=b'State/Province', blank=True)),
                ('postal_code', models.CharField(max_length=10, verbose_name=b'Postal Code')),
                ('geom', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True)),
                ('geocode_results', jsonfield.fields.JSONField(null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'Addresses',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('iso_code', models.CharField(max_length=2, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=45)),
            ],
            options={
                'ordering': ['name', 'iso_code'],
                'verbose_name_plural': 'Countries',
            },
        ),
        migrations.AddField(
            model_name='address',
            name='country',
            field=models.ForeignKey(to='firecares_core.Country'),
        ),
        migrations.AlterUniqueTogether(
            name='address',
            unique_together=set([('address_line1', 'address_line2', 'postal_code', 'city', 'state_province', 'country')]),
        ),
    ]
