# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CountyorEquivalent'
        db.create_table(u'usgs_countyorequivalent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('state_fipscode', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('state_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('county_fipscode', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('county_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('stco_fipscode', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['CountyorEquivalent'])

        # Adding model 'StateorTerritoryHigh'
        db.create_table(u'usgs_stateorterritoryhigh', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('state_fipscode', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('state_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['StateorTerritoryHigh'])

        # Adding model 'IncorporatedPlace'
        db.create_table(u'usgs_incorporatedplace', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('state_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('place_fipscode', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
            ('place_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('iscapitalcity', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('iscountyseat', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['IncorporatedPlace'])

        # Adding model 'NativeAmericanArea'
        db.create_table(u'usgs_nativeamericanarea', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('nativeamericanarea_fipscode', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
            ('admintype', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['NativeAmericanArea'])

        # Adding model 'UnincorporatedPlace'
        db.create_table(u'usgs_unincorporatedplace', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('state_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('place_fipscode', self.gf('django.db.models.fields.CharField')(max_length=5, null=True, blank=True)),
            ('place_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['UnincorporatedPlace'])

        # Adding model 'CongressionalDistrict'
        db.create_table(u'usgs_congressionaldistrict', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('designation', self.gf('django.db.models.fields.CharField')(max_length=60, null=True, blank=True)),
            ('state_fipscode', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('state_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('admintype', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('ownerormanagingagency', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['CongressionalDistrict'])

        # Adding model 'Reserve'
        db.create_table(u'usgs_reserve', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('admintype', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('ownerormanagingagency', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['Reserve'])

        # Adding model 'MinorCivilDivision'
        db.create_table(u'usgs_minorcivildivision', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('state_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('minorcivildivision_fipscode', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('minorcivildivision_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['MinorCivilDivision'])


    def backwards(self, orm):
        # Deleting model 'CountyorEquivalent'
        db.delete_table(u'usgs_countyorequivalent')

        # Deleting model 'StateorTerritoryHigh'
        db.delete_table(u'usgs_stateorterritoryhigh')

        # Deleting model 'IncorporatedPlace'
        db.delete_table(u'usgs_incorporatedplace')

        # Deleting model 'NativeAmericanArea'
        db.delete_table(u'usgs_nativeamericanarea')

        # Deleting model 'UnincorporatedPlace'
        db.delete_table(u'usgs_unincorporatedplace')

        # Deleting model 'CongressionalDistrict'
        db.delete_table(u'usgs_congressionaldistrict')

        # Deleting model 'Reserve'
        db.delete_table(u'usgs_reserve')

        # Deleting model 'MinorCivilDivision'
        db.delete_table(u'usgs_minorcivildivision')


    models = {
        u'usgs.congressionaldistrict': {
            'Meta': {'object_name': 'CongressionalDistrict'},
            'admintype': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'designation': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ownerormanagingagency': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'}),
            'state_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        },
        u'usgs.countyorequivalent': {
            'Meta': {'object_name': 'CountyorEquivalent'},
            'county_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'county_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'}),
            'state_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'stco_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'})
        },
        u'usgs.govunits': {
            'Meta': {'ordering': "('state_name', 'county_name')", 'object_name': 'GovUnits'},
            'county_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'county_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fips': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'}),
            'state_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        },
        u'usgs.incorporatedplace': {
            'Meta': {'object_name': 'IncorporatedPlace'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iscapitalcity': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'iscountyseat': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'place_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'place_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        },
        u'usgs.minorcivildivision': {
            'Meta': {'object_name': 'MinorCivilDivision'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'minorcivildivision_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'minorcivildivision_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        },
        u'usgs.nativeamericanarea': {
            'Meta': {'object_name': 'NativeAmericanArea'},
            'admintype': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'nativeamericanarea_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'})
        },
        u'usgs.reserve': {
            'Meta': {'object_name': 'Reserve'},
            'admintype': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ownerormanagingagency': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'})
        },
        u'usgs.stateorterritoryhigh': {
            'Meta': {'object_name': 'StateorTerritoryHigh'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'}),
            'state_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        },
        u'usgs.unincorporatedplace': {
            'Meta': {'object_name': 'UnincorporatedPlace'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'place_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'place_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'population': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'}),
            'state_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['usgs']