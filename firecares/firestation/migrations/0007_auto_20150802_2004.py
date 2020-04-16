# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    def migrate_data(apps, schema_editor):
        FD = apps.get_model("firestation", "firedepartment")
        departments = [81472, 75500, 77379, 74121, 77549, 87256, 88403, 88490,
                       88539, 89649, 91934, 77867, 94653, 79277, 87291, 73343,
                       73847, 74286, 77197, 78139, 78456, 78503, 79639, 80595,
                       81835, 77661, 84453, 84578, 84888, 77707, 85484, 77727,
                       87166, 88821, 88856, 90810, 90950, 91031, 91907, 92545,
                       92916, 94042, 94250, 94264, 94268, 97477, 97491, 98190,
                       98606, 77629]
        FD.objects.filter(id__in=departments).update(featured=True)
        FD.objects.filter(id=81472).update(fdid=20014)

    dependencies = [
        ('firestation', '0006_auto_20150731_0747'),
    ]

    operations = [
    ]
