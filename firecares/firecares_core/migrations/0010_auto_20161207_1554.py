# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0003_auto_20151126_1523'),
        ('firestation', '0030_auto_20161123_1349'),
        ('firecares_core', '0009_registrationwhitelist'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentInvitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('department', models.ForeignKey(to='firestation.FireDepartment')),
                ('invitation', annoying.fields.AutoOneToOneField(to='invitations.Invitation')),
            ],
        ),
        migrations.AlterField(
            model_name='registrationwhitelist',
            name='email_or_domain',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]
