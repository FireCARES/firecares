# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0005_accountrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountrequest',
            name='email',
            field=models.EmailField(unique=True, max_length=254),
        ),
    ]
