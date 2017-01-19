# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0020_auto_20170119_1021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentassociationrequest',
            name='permission',
            field=models.CharField(default=b'admin_firedepartment', max_length=100),
        ),
    ]
