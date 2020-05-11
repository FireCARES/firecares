# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0003_contactrequest_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='address_line2',
            field=models.CharField(max_length=100, null=True, verbose_name=b'Address line 2', blank=True),
        ),
    ]
