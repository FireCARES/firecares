# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0020_update_greeley_headquarters_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='iaff',
            field=models.CharField(max_length=25, null=True, blank=True),
        ),
    ]
