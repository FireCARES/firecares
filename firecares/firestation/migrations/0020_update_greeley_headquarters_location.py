# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.geos import Point
from django.db import models, migrations
from genericm2m.utils import monkey_patch


class Migration(migrations.Migration):

    dependencies = [
        ('firestation', '0019_assign-station-number-2'),
        ('usgs', '0003_auto_20151105_2156')
    ]

    def update_greeley_headquarters_location(apps, schema_editor):
        FD = apps.get_model("firestation", "firedepartment")
        IP = apps.get_model("usgs", "IncorporatedPlace")
        # Have to patch this in since RelatedObjectsDescriptor won't be attached
        monkey_patch(FD, 'government_unit')
        greeley = IP.objects.filter(place_name='Greeley', state_name='Colorado').first()
        fd = FD.objects.filter(id=97668).first()
        if fd:
            fd.headquarters_address.geom = Point(-104.694001, 40.426638)
            fd.headquarters_address.save()
            fd.geom = greeley.geom
            fd.government_unit.connect(greeley)
            fd.population = greeley.population
            fd.save()

    operations = [
        migrations.RunPython(update_greeley_headquarters_location)
    ]
