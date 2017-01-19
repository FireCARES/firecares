# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0037_auto_20170111_1000'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('firecares_core', '0016_userprofile_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationwhitelist',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='registrationwhitelist',
            name='created_by',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='registrationwhitelist',
            name='department',
            field=models.ForeignKey(blank=True, to='firestation.FireDepartment', null=True),
        ),
    ]
