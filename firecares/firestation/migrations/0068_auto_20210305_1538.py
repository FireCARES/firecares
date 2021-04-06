# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0067_auto_20210223_1052'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='drivetimegeom_014',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='drivetimegeom_15_26',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='drivetimegeom_27_42',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='drivetimegeom_38_plus',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='drivetimegeom_43_plus',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='parcelcount_high38_plus',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='parcelcount_high_43_plus',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='parcelcount_low_15_26',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='parcelcount_medium_27_42',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='parcelcount_unknown_15_26',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_high38_plus',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_high_43_plus',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_low_15_26',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_medium_27_42',
        ),
        migrations.RemoveField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_unknown_15_26',
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='erf_area_high',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='erf_area_low',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='erf_area_medium',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='erf_area_unknown',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='parcel_count_high',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='parcel_count_low',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='parcel_count_medium',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='parcel_count_unknown',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='percent_covered_high',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='percent_covered_low',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='percent_covered_medium',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='percent_covered_unknown',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='firestation',
            name='erf_area_high',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='firestation',
            name='erf_area_low',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='firestation',
            name='erf_area_medium',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='firestation',
            name='erf_area_unknown',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True),
        ),
    ]
