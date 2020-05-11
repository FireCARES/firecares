# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0021_firedepartment_iaff'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='twitter_handle',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
