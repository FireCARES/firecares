# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0029_auto_20161122_1420'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='firedepartment',
            options={'ordering': ('name',), 'permissions': (('admin_firedepartment', 'Can administer department users'),)},
        ),
    ]
