# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('firestation', '0038_firedepartment_domain_name'),
        ('firecares_core', '0022_auto_20170120_1131'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountrequest',
            name='approved_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='accountrequest',
            name='approved_by',
            field=models.ForeignKey(related_name='approved_by_set', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='accountrequest',
            name='department',
            field=models.ForeignKey(blank=True, to='firestation.FireDepartment', null=True),
        ),
    ]
