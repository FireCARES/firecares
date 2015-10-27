# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0017_auto_20151006_1453'),
    ]

    operations = [
        migrations.RunSQL("CREATE extension fuzzystrmatch"),
        migrations.RunSQL("CREATE extension pg_trgm"),
    ]
