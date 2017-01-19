# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import firecares.firecares_core.models


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0019_auto_20170118_1034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentassociationrequest',
            name='permission',
            field=models.ForeignKey(default=firecares.firecares_core.models.default_requested_permission, to='auth.Permission'),
        ),
    ]
