# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0004_firedepartment_featured'),
    ]

    operations = [
        migrations.AlterField(
            model_name='firedepartment',
            name='dist_model_score',
            field=models.FloatField(db_index=True, null=True, editable=False, blank=True),
        ),
    ]
