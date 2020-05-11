# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0037_auto_20170111_1000'),
        ('firecares_core', '0015_userprofile_functional_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='department',
            field=models.ForeignKey(blank=True, to='firestation.FireDepartment', null=True),
        ),
    ]
