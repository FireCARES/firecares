# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import phonenumber_field.modelfields
import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FireDepartment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('fdid', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=100)),
                ('headquarters_phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True, blank=True)),
                ('headquarters_fax', phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True, blank=True)),
                ('department_type', models.CharField(blank=True, max_length=20, null=True, choices=[(b'Volunteer', b'Volunteer'), (b'Mostly Volunteer', b'Mostly Volunteer'), (b'Career', b'Career'), (b'Mostly Career', b'Mostly Career')])),
                ('organization_type', models.CharField(max_length=75, null=True, blank=True)),
                ('website', models.URLField(null=True, blank=True)),
                ('state', models.CharField(max_length=2)),
                ('region', models.CharField(blank=True, max_length=20, null=True, choices=[(b'Northeast', b'Northeast'), (b'West', b'West'), (b'South', b'South'), (b'Midwest', b'Midwest'), (None, b'')])),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('dist_model_score', models.FloatField(null=True, editable=False, blank=True)),
                ('population', models.IntegerField(null=True, blank=True)),
                ('headquarters_address', models.ForeignKey(related_name='firedepartment_headquarters', blank=True, to='firecares_core.Address', null=True)),
                ('mail_address', models.ForeignKey(blank=True, to='firecares_core.Address', null=True)),
            ],
            options={
                'ordering': ('state', 'name'),
            },
        ),
        migrations.CreateModel(
            name='NFIRSStatistic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('metric', models.CharField(max_length=50, db_index=True)),
                ('year', models.PositiveSmallIntegerField(db_index=True)),
                ('count', models.PositiveSmallIntegerField(null=True, db_index=True)),
                ('fire_department', models.ForeignKey(to='firestation.FireDepartment')),
            ],
            options={
                'ordering': ['-year'],
            },
        ),
        migrations.CreateModel(
            name='Staffing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('apparatus', models.CharField(default=b'Engine', max_length=20, choices=[(b'Engine', b'Engine'), (b'Ladder/Truck/Aerial', b'Ladder/Truck/Aerial'), (b'Quint', b'Quint'), (b'Ambulance/ALS', b'Ambulance/ALS'), (b'Ambulance/BLS', b'Ambulance/BLS'), (b'Heavy Rescue', b'Heavy Rescue'), (b'Boat', b'Boat'), (b'Hazmat', b'Hazmat'), (b'Chief', b'Chief'), (b'Other', b'Other')])),
                ('firefighter', models.PositiveIntegerField(default=0, max_length=2, null=True, blank=True, validators=[django.core.validators.MaxValueValidator(99)])),
                ('firefighter_emt', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99)], max_length=2, blank=True, null=True, verbose_name=b'Firefighter EMT')),
                ('firefighter_paramedic', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99)], max_length=2, blank=True, null=True, verbose_name=b'Firefighter Paramedic')),
                ('ems_emt', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99)], max_length=2, blank=True, null=True, verbose_name=b'EMS-Only EMT')),
                ('ems_paramedic', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99)], max_length=2, blank=True, null=True, verbose_name=b'EMS-Only Paramedic')),
                ('officer', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99)], max_length=2, blank=True, null=True, verbose_name=b'Company/Unit Officer')),
                ('officer_paramedic', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99)], max_length=2, blank=True, null=True, verbose_name=b'Company/Unit Officer Paramedic')),
                ('ems_supervisor', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99)], max_length=2, blank=True, null=True, verbose_name=b'EMS Supervisor')),
                ('chief_officer', models.PositiveIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(99)], max_length=2, blank=True, null=True, verbose_name=b'Cheif Officer')),
            ],
            options={
                'verbose_name_plural': 'Response Capabilities',
            },
        ),
        migrations.CreateModel(
            name='USGSStructureData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('objectid', models.IntegerField(unique=True, null=True, blank=True)),
                ('permanent_identifier', models.CharField(max_length=40, null=True, blank=True)),
                ('source_featureid', models.CharField(max_length=40, null=True, blank=True)),
                ('source_datasetid', models.CharField(max_length=40, null=True, blank=True)),
                ('source_datadesc', models.CharField(max_length=100, null=True, blank=True)),
                ('source_originator', models.CharField(max_length=130, null=True, blank=True)),
                ('data_security', models.IntegerField(blank=True, null=True, choices=[(0, b'Unknown'), (1, b'Top Secret'), (2, b'Secret'), (3, b'Confidential'), (4, b'Restricted'), (5, b'Unclassified'), (6, b'Sensitive')])),
                ('distribution_policy', models.CharField(blank=True, max_length=4, null=True, choices=[(b'A1', b'Emergency Service Provider - Internal Use Only'), (b'A2', b'Emergency Service Provider - Bitmap Display Via Web'), (b'A3', b'Emergency Service Provider - Free Distribution to Third Parties'), (b'A4', b'Emergency Service Provider - Free Distribution to Third Parties Via Internet'), (b'B1', b'Government Agencies or Their Delegated Agents - Internal Use Only'), (b'B2', b'Government Agencies or Their Delegated Agents - Bitmap Display Via Web'), (b'B3', b'Government Agencies or Their Delegated Agents - Free Distribution to Third Parties'), (b'B4', b'Government Agencies or Their Delegated Agents - Free Distribution to Third Parties Via Internet'), (b'C1', b'Other Public or Educational Institutions - Internal Use Only'), (b'C2', b'Other Public or Educational Institutions - Bitmap Display Via Web'), (b'C3', b'Other Public or Educational Institutions - Free Distribution to Third Parties'), (b'C4', b'Other Public or Educational Institutions - Free Distribution to Third Parties Via Internet'), (b'D1', b'Data Contributors - Internal Use Only'), (b'D2', b'Data Contributors - Bitmap Display Via Web'), (b'D3', b'Data Contributors - Free Distribution to Third Parties'), (b'D4', b'Data Contributors - Free Distribution to Third Parties Via Internet'), (b'E1', b'Public Domain - Internal Use Only'), (b'E2', b'Public Domain - Bitmap Display Via Web'), (b'E3', b'Public Domain - Free Distribution to Third Parties'), (b'E4', b'Public Domain - Free Distribution to Third Parties Via Internet')])),
                ('loaddate', models.DateTimeField(null=True, blank=True)),
                ('ftype', models.CharField(max_length=50, null=True, blank=True)),
                ('fcode', models.IntegerField(blank=True, null=True, choices=[(81000, b'Transportation Facility'), (81006, b'Airport Terminal'), (81008, b'Air Support / Maintenance Facility'), (81010, b'Air Traffic Control Center / Command Center'), (81011, b'Boat Ramp / Dock'), (81012, b'Bridge'), (81014, b'Bridge:  Light Rail / Subway'), (81016, b'Bridge:  Railroad'), (81018, b'Bridge:  Road'), (81020, b'Border Crossing / Port of Entry'), (81022, b'Bus Station / Dispatch Facility'), (81024, b'Ferry Terminal / Dispatch Facility'), (81025, b'Harbor / Marina'), (81026, b'Helipad / Heliport / Helispot'), (81028, b'Launch Facility'), (81030, b'Launch Pad'), (81032, b'Light Rail Power Substation'), (81034, b'Light Rail Station'), (81036, b'Park and Ride / Commuter Lot'), (81038, b'Parking Lot Structure / Garage'), (81040, b'Pier / Wharf / Quay / Mole'), (81042, b'Port Facility'), (81044, b'Port Facility: Commercial Port'), (81046, b'Port Facility: Crane'), (81048, b'Port Facility: Maintenance and Fuel Facility'), (81050, b'Port Facility: Modal Transfer Facility'), (81052, b'Port Facility: Passenger Terminal'), (81054, b'Port Facility: Warehouse Storage / Container Yard'), (81056, b'Railroad Facility'), (81058, b'Railroad Command / Control Facility'), (81060, b'Railroad Freight Loading Facility'), (81062, b'Railroad Maintenance / Fuel Facility'), (81064, b'Railroad Roundhouse / Turntable'), (81066, b'Railroad Station'), (81068, b'Railroad Yard'), (81070, b'Rest Stop / Roadside Park'), (81072, b'Seaplane Anchorage / Base'), (81073, b'Snowshed'), (81074, b'Subway Station'), (81076, b'Toll Booth / Plaza'), (81078, b'Truck Stop'), (81080, b'Tunnel'), (81082, b'Tunnel:  Light Rail / Subway'), (81084, b'Tunnel:  Road'), (81086, b'Tunnel:  Railroad'), (81088, b'Weigh Station / Inspection Station')])),
                ('name', models.CharField(max_length=100, null=True, blank=True)),
                ('islandmark', models.IntegerField(blank=True, null=True, verbose_name=b'Landmark', choices=[(1, b'Yes'), (2, b'No'), (0, b'Unknown')])),
                ('pointlocationtype', models.IntegerField(blank=True, null=True, verbose_name=b'Point Type', choices=[(0, b'Unknown'), (1, b'Centroid'), (2, b'Egress or Entrance'), (3, b'Turn-off location'), (4, b'Approximate')])),
                ('admintype', models.IntegerField(blank=True, null=True, choices=[(0, b'Unknown'), (1, b'Federal'), (2, b'Tribal'), (3, b'State'), (4, b'Regional'), (5, b'County'), (6, b'Municipal'), (7, b'Private')])),
                ('addressbuildingname', models.CharField(max_length=60, null=True, verbose_name=b'Building Name', blank=True)),
                ('address', models.CharField(max_length=75, null=True, blank=True)),
                ('city', models.CharField(max_length=40, null=True, blank=True)),
                ('state', models.CharField(max_length=2, null=True, blank=True)),
                ('zipcode', models.CharField(max_length=10, null=True, blank=True)),
                ('gnis_id', models.CharField(max_length=10, null=True, blank=True)),
                ('foot_id', models.CharField(max_length=40, null=True, blank=True)),
                ('complex_id', models.CharField(max_length=40, null=True, blank=True)),
                ('globalid', models.CharField(max_length=38, null=True, blank=True)),
                ('geom', django.contrib.gis.db.models.fields.PointField(srid=4326)),
            ],
            options={
                'ordering': ('state', 'city', 'name'),
            },
        ),
        migrations.CreateModel(
            name='FireStation',
            fields=[
                ('usgsstructuredata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='firestation.USGSStructureData')),
                ('fdid', models.CharField(max_length=10, null=True, blank=True)),
                ('station_number', models.IntegerField(null=True, blank=True)),
                ('district', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='firestation.FireDepartment', null=True)),
                ('station_address', models.ForeignKey(blank=True, to='firecares_core.Address', null=True)),
            ],
            options={
                'verbose_name': 'Fire Station',
            },
            bases=('firestation.usgsstructuredata',),
        ),
        migrations.AddField(
            model_name='staffing',
            name='firestation',
            field=models.ForeignKey(to='firestation.FireStation'),
        ),
        migrations.AlterUniqueTogether(
            name='nfirsstatistic',
            unique_together=set([('fire_department', 'year', 'metric')]),
        ),
    ]
