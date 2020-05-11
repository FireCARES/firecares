# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0025_auto_20170324_1337'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationwhitelist',
            name='permissions_applied',
            field=models.BooleanField(default=False),
        ),
    ]
