# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0014_auto_20170111_1428'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='functional_title',
            field=models.CharField(max_length=250, null=True, blank=True),
        ),
    ]
