# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0063_firedepartment_additional_fdids'),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(null=True, blank=True)),
                ('parent_department', models.OneToOneField(related_name='note', null=True, blank=True, to='firestation.FireDepartment')),
                ('parent_station', models.OneToOneField(related_name='note', null=True, blank=True, to='firestation.FireStation')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='note',
            unique_together=set([('parent_department', 'parent_station')]),
        ),
    ]
