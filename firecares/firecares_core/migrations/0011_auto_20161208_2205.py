# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0010_auto_20161207_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentinvitation',
            name='department',
            field=models.ForeignKey(to='firestation.FireDepartment', null=True),
        ),
    ]
