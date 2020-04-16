# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0002_contactrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactrequest',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2015, 12, 15, 3, 6, 36, 732718, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
