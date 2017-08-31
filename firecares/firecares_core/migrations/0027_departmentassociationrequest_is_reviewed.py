# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0026_registrationwhitelist_permissions_applied'),
    ]

    operations = [
        migrations.AddField(
            model_name='departmentassociationrequest',
            name='is_reviewed',
            field=models.BooleanField(default=False),
        ),
    ]
