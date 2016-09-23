# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import firecares.firestation.models


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0026_auto_20160806_1250'),
    ]

    operations = [
        migrations.CreateModel(
            name='IntersectingDepartmentLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(related_name='intersecting_department', to='firestation.FireDepartment')),
                ('removed_department', models.ForeignKey(related_name='removed_intersecting_departments', to='firestation.FireDepartment')),
            ],
        )
    ]
