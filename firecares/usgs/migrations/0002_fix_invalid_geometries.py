# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forwards(apps, schema_editor):
    print ' -- These migrations might take awhile (10-15 minutes)'
    schema_editor.execute("ALTER TABLE usgs_incorporatedplace ALTER COLUMN geom TYPE geometry(MultiPolygon,4326) USING ST_Multi(geom);")
    print 'usgs_incorporatedplace geom column is MultiPolygon (1/12)'
    schema_editor.execute("UPDATE usgs_incorporatedplace SET geom = ST_MakeValid(geom);")
    print 'usgs_incorporatedplace geom is valid (2/12)'
    schema_editor.execute("ALTER TABLE usgs_unincorporatedplace ALTER COLUMN geom TYPE geometry(MultiPolygon,4326) USING ST_Multi(geom);")
    print 'usgs_unincorporatedplace geom column is MultiPolygon (3/12)'
    schema_editor.execute("UPDATE usgs_unincorporatedplace SET geom = ST_MakeValid(geom);")
    print 'usgs_unincorporatedplace geom is valid (4/12)'
    schema_editor.execute("ALTER TABLE usgs_reserve ALTER COLUMN geom TYPE geometry(MultiPolygon,4326) USING ST_Multi(geom);")
    print 'usgs_reserve geom column is MultiPolygon (5/12)'
    schema_editor.execute("UPDATE usgs_reserve SET geom = ST_MakeValid(geom);")
    print 'usgs_reserve geom is valid (6/12)'
    schema_editor.execute("ALTER TABLE usgs_countyorequivalent ALTER COLUMN geom TYPE geometry(MultiPolygon,4326) USING ST_Multi(geom);")
    print 'usgs_countyorequivalent geom column is MultiPolygon (7/12)'
    schema_editor.execute("UPDATE usgs_countyorequivalent SET geom = ST_MakeValid(geom);")
    print 'usgs_countyorequivalent geom is valid (8/12)'
    schema_editor.execute("ALTER TABLE usgs_minorcivildivision ALTER COLUMN geom TYPE geometry(MultiPolygon,4326) USING ST_Multi(geom);")
    print 'usgs_minorcivildivision geom column is MultiPolygon (9/12)'
    schema_editor.execute("UPDATE usgs_minorcivildivision SET geom = ST_MakeValid(geom);")
    print 'usgs_minorcivildivision geom is valid (10/12)'
    schema_editor.execute("ALTER TABLE usgs_nativeamericanarea ALTER COLUMN geom TYPE geometry(MultiPolygon,4326) USING ST_Multi(geom);")
    print 'usgs_nativeamericanarea geom column is MultiPolygon (11/12)'
    schema_editor.execute("UPDATE usgs_nativeamericanarea SET geom = ST_MakeValid(geom);")
    print 'usgs_nativeamericanarea geom is valid (12/12)'

class Migration(migrations.Migration):
    dependencies = [
        ('usgs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, reverse_code=migrations.RunPython.noop)
    ]
