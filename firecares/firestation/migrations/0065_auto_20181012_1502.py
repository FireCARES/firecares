# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0064_auto_20180426_1455'),
    ]

    sql = """
update firestation_firedepartment
set department_type = 'Combination'
where trim(department_type) = 'Mostly Volunteer' or trim(department_type) = 'Mostly Career';
"""

    operations = [
        migrations.RunSQL(sql),
        migrations.AlterField(
            model_name='firedepartment',
            name='department_type',
            field=models.CharField(blank=True, max_length=20, null=True, choices=[(b'Volunteer', b'Volunteer'), (b'Career', b'Career'), (b'Combination', b'Combination')]),
        ),
    ]
