# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0018_departmentassociationrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='departmentassociationrequest',
            name='denied_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='departmentassociationrequest',
            name='approved_by',
            field=models.ForeignKey(related_name='approved_association_requests_set', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='departmentassociationrequest',
            name='denied_by',
            field=models.ForeignKey(related_name='denied_assocation_requests_set', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='departmentassociationrequest',
            name='permission',
            field=models.ForeignKey(default=55, to='auth.Permission'),
        ),
        migrations.AlterUniqueTogether(
            name='registrationwhitelist',
            unique_together=set([('department', 'email_or_domain')]),
        ),
    ]
