# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0008_auto_20150805_1702'),
    ]

    def migrate_data(apps, schema_editor):
        FD = apps.get_model("firestation", "firedepartment")
        for dept in FD.objects.filter(risk_model_fires_structure__isnull=False):
            # Set new percentage to the current value and update the current value to be the actual count.
            if getattr(dept, 'risk_model_fires_floor_percentage', None):
                dept.risk_model_fires_floor_percentage = dept.risk_model_fires_floor
                dept.risk_model_fires_floor = dept.risk_model_fires_room * dept.risk_model_fires_floor_percentage
                dept.risk_model_fires_structure_percentage = dept.risk_model_fires_structure
                dept.risk_model_fires_structure = dept.risk_model_fires_room * dept.risk_model_fires_structure_percentage
                dept.save()


    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_floor_percentage',
            field=models.FloatField(null=True, verbose_name=b'Percentage of fires confined to the floor of origin.', blank=True),
        ),
        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_structure_percentage',
            field=models.FloatField(null=True, verbose_name=b'Percentage of fires spread beyond the building of origin', blank=True),
        ),
        #migrations.RunPython(migrate_data),
    ]
