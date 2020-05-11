# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db import transaction

class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0009_auto_20150807_1552'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of fires per year.', blank=True),
        ),

        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_size0_percentage',
            field=models.FloatField(null=True, verbose_name=b'Percentage of size 0 fires.', blank=True),
        ),

        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_size0',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of size 0 fires.', blank=True),
        ),


        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_size1',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of size 1 fires.', blank=True),
        ),

        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_size1_percentage',
            field=models.FloatField(null=True, verbose_name=b'Percentage of size 1 fires.', blank=True),
        ),

        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_size2',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of size 2 firese.', blank=True),
        ),

        migrations.AddField(
            model_name='firedepartment',
            name='risk_model_fires_size2_percentage',
            field=models.FloatField(null=True, verbose_name=b'Percentage of size 2 fires.', blank=True),
        ),

        migrations.RunSQL("UPDATE firestation_firedepartment SET risk_model_fires=risk_model_fires_room;"),
        migrations.RunSQL("UPDATE firestation_firedepartment SET risk_model_fires_size0_percentage=1-risk_model_fires_floor_percentage-risk_model_fires_structure_percentage;"),
        migrations.RunSQL("UPDATE firestation_firedepartment SET risk_model_fires_size0=risk_model_fires*risk_model_fires_size0_percentage;"),
        migrations.RunSQL("UPDATE firestation_firedepartment SET risk_model_fires_size1=risk_model_fires_floor;"),
        migrations.RunSQL("UPDATE firestation_firedepartment SET risk_model_fires_size1_percentage=risk_model_fires_floor_percentage;"),
        migrations.RunSQL("UPDATE firestation_firedepartment SET risk_model_fires_size2=risk_model_fires_structure;"),
        migrations.RunSQL("UPDATE firestation_firedepartment SET risk_model_fires_size2_percentage=risk_model_fires_structure_percentage;"),
    ]
