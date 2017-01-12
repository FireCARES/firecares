# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firecares_core', '0013_predetermineduser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='predetermineduser',
            name='email',
            field=models.EmailField(unique=True, max_length=254),
        ),
        migrations.AlterUniqueTogether(
            name='predetermineduser',
            unique_together=set([('email', 'department')]),
        ),
    ]
