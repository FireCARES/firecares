# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0056_effectivefirefightingforcelevel_drivetimegeom_38_plus'),
    ]

    operations = [
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='parcelcount_high38_plus',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_high38_plus',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_high_43_plus',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_low_15_26',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_medium_27_42',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='effectivefirefightingforcelevel',
            name='perc_covered_unknown_15_26',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
