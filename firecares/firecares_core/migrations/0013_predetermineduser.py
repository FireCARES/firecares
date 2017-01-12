# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0037_auto_20170111_1000'),
        ('firecares_core', '0012_departmentinvitation_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='PredeterminedUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('first_name', models.CharField(max_length=30)),
                ('last_name', models.CharField(max_length=30)),
                ('department', models.ForeignKey(to='firestation.FireDepartment')),
            ],
        ),
    ]
