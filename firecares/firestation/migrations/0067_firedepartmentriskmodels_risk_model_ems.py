# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0066_staffing_other_apparatus_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartmentriskmodels',
            name='risk_model_ems',
            field=models.FloatField(db_index=True, null=True, verbose_name=b'Predicted number of EMS incidents per year.', blank=True),
        ),
    ]
