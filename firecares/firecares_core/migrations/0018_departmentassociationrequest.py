# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0037_auto_20170111_1000'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('firecares_core', '0017_auto_20170112_1248'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentAssociationRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('approved_at', models.DateTimeField(null=True, blank=True)),
                ('message', models.TextField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('approved_by', models.ForeignKey(related_name='approved_by_set', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('denied_by', models.ForeignKey(related_name='denied_by_set', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('department', models.ForeignKey(to='firestation.FireDepartment')),
                ('permission', models.ForeignKey(to='auth.Permission')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
