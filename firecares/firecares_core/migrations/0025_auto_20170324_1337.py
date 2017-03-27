# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('firecares_core', '0024_auto_20170125_1411'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactrequest',
            name='completed_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='contactrequest',
            name='completed_by',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='registrationwhitelist',
            name='permission',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
