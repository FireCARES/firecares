# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0021_auto_20170119_1200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registrationwhitelist',
            name='email_or_domain',
            field=models.CharField(max_length=200),
        ),
    ]
