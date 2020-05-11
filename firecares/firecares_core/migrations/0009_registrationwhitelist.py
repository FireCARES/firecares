# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0008_auto_20161122_1420'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationWhitelist',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email_or_domain', models.CharField(unique=True, max_length=254)),
            ],
        ),
    ]
