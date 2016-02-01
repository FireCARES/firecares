# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0004_mediaitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaitem',
            name='is_shown',
            field=models.BooleanField(default=True),
        ),
    ]
