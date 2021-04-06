# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0006_auto_20181015_1358'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departmentwarnings',
            name='warningname',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='weatherwarnings',
            name='warnid',
            field=models.CharField(max_length=200, blank=True),
        ),
    ]
