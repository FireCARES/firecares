# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('firecares_core', '0023_auto_20170120_2139'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountrequest',
            name='denied_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='accountrequest',
            name='denied_by',
            field=models.ForeignKey(related_name='denied_by_set', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
