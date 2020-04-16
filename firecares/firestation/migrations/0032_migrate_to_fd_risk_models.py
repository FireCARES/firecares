# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def forwards(apps, schema_editor):
    FireDepartment = apps.get_model('firestation', 'FireDepartment')
    FireDepartmentRiskModels = apps.get_model('firestation', 'FireDepartmentRiskModels')

    instances = []
    for fd in FireDepartment.objects.all():
        # Will default to "low" level
        rm = FireDepartmentRiskModels()
        rm.department = fd
        rm.dist_model_score = fd.dist_model_score
        rm.risk_model_deaths = fd.risk_model_deaths
        rm.risk_model_injuries = fd.risk_model_injuries
        rm.risk_model_fires = fd.risk_model_fires
        rm.risk_model_fires_size0 = fd.risk_model_fires_size0
        rm.risk_model_fires_size0_percentage = fd.risk_model_fires_size0_percentage
        rm.risk_model_fires_size1 = fd.risk_model_fires_size1
        rm.risk_model_fires_size1_percentage = fd.risk_model_fires_size1_percentage
        rm.risk_model_fires_size2 = fd.risk_model_fires_size2
        rm.risk_model_fires_size2_percentage = fd.risk_model_fires_size2_percentage
        instances.append(rm)
    FireDepartmentRiskModels.objects.bulk_create(instances)


def backwards(apps, schema_editor):
    FireDepartmentRiskModels = apps.get_model('firestation', 'FireDepartmentRiskModels')
    FireDepartmentRiskModels.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0031_create_fd_risk_models'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
