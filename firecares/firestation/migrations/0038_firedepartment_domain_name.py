# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0037_auto_20170111_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='domain_name',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
