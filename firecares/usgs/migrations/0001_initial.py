# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GovUnits'
        db.create_table(u'usgs_govunits', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('objectid', self.gf('django.db.models.fields.IntegerField')(unique=True, null=True, blank=True)),
            ('permanent_identifier', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_featureid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datasetid', self.gf('django.db.models.fields.CharField')(max_length=40, null=True, blank=True)),
            ('source_datadesc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('source_originator', self.gf('django.db.models.fields.CharField')(max_length=130, null=True, blank=True)),
            ('data_security', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('distribution_policy', self.gf('django.db.models.fields.CharField')(max_length=4, null=True, blank=True)),
            ('loaddate', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ftype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('fcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('state_fipscode', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('state_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('county_fipscode', self.gf('django.db.models.fields.CharField')(max_length=3, null=True, blank=True)),
            ('county_name', self.gf('django.db.models.fields.CharField')(max_length=120, null=True, blank=True)),
            ('population', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('gnis_id', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('fips', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('globalid', self.gf('django.db.models.fields.CharField')(max_length=38, null=True, blank=True)),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PolygonField')()),
        ))
        db.send_create_signal(u'usgs', ['GovUnits'])


    def backwards(self, orm):
        # Deleting model 'GovUnits'
        db.delete_table(u'usgs_govunits')


    models = {
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
        }
    }

    complete_apps = ['usgs']