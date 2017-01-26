# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0038_firedepartment_domain_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='firedepartment',
            name='domain_name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
