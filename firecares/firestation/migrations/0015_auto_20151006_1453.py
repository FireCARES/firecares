# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forwards_func(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    FireStation = apps.get_model("firestation", "FireStation")
    db_alias = schema_editor.connection.alias
    FireStation.objects.using(db_alias).filter(state='VA', department__isnull=True, name__icontains='Chesterfield').update(department=77353)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Hanover County Fire / Emergency Medical Services Company').update(department=83555)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Loudoun County Fire and Rescue').update(department=87281)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Navy Regional Mid').update(department=89704)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Goochland County Volunteer').update(department=82690)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Dale City Volunteer').update(department=92724)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Chancellor Volunteer Fire', department__isnull=True).update(department=95808)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Shenandoah County Fire').update(department=94942)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Spotsylvania').update(department=95808)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Metropolitan Washington Airport Authority').update(department=88514)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='King George').update(department=85748)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Caroline County').update(department=76684)

def reverse_func(apps, schema_editor):
    FireStation = apps.get_model("firestation", "FireStation")
    db_alias = schema_editor.connection.alias
    FireStation.objects.using(db_alias).filter(state='VA', department__isnull=True, name__icontains='Chesterfield').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Hanover County Fire / Emergency Medical Services Company').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Loudoun County Fire and Rescue').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Navy Regional Mid').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Goochland County Volunteer').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Dale City Volunteer').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Chancellor Volunteer Fire', department__isnull=True).update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Shenandoah County Fire').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Spotsylvania').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Metropolitan Washington Airport Authority').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='King George').update(department=None)
    FireStation.objects.using(db_alias).filter(state='VA',  name__icontains='Caroline County').update(department=None)


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0014_auto_20151006_1131'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]
