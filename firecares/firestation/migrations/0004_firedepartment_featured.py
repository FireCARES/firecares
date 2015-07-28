# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0003_auto_20150728_1215'),
    ]

    def update_depts(apps, schema_editor):
        fd = apps.get_model("firestation", "FireDepartment")

        priority_depts = [73375, 73842, 74121, 75500, 77177, 77379, 77549, 77629, 77867, 87256,
                          88403, 88490, 88539, 89649, 91934, 94653, 99996]

        fd.objects.filter(id__in=priority_depts).update(featured=True)

    operations = [
        migrations.AddField(
            model_name='firedepartment',
            name='featured',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.RunPython(update_depts)
    ]
