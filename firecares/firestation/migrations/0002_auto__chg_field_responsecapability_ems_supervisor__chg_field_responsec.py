# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'ResponseCapability.ems_supervisor'
        db.alter_column(u'firestation_responsecapability', 'ems_supervisor', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

        # Changing field 'ResponseCapability.officer_paramedic'
        db.alter_column(u'firestation_responsecapability', 'officer_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

        # Changing field 'ResponseCapability.firefighter'
        db.alter_column(u'firestation_responsecapability', 'firefighter', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

        # Changing field 'ResponseCapability.firefighter_emt'
        db.alter_column(u'firestation_responsecapability', 'firefighter_emt', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

        # Changing field 'ResponseCapability.chief_officer'
        db.alter_column(u'firestation_responsecapability', 'chief_officer', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

        # Changing field 'ResponseCapability.firefighter_paramedic'
        db.alter_column(u'firestation_responsecapability', 'firefighter_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

        # Changing field 'ResponseCapability.ems_emt'
        db.alter_column(u'firestation_responsecapability', 'ems_emt', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

        # Changing field 'ResponseCapability.ems_paramedic'
        db.alter_column(u'firestation_responsecapability', 'ems_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

        # Changing field 'ResponseCapability.officer'
        db.alter_column(u'firestation_responsecapability', 'officer', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2, null=True))

    def backwards(self, orm):

        # Changing field 'ResponseCapability.ems_supervisor'
        db.alter_column(u'firestation_responsecapability', 'ems_supervisor', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'ResponseCapability.officer_paramedic'
        db.alter_column(u'firestation_responsecapability', 'officer_paramedic', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'ResponseCapability.firefighter'
        db.alter_column(u'firestation_responsecapability', 'firefighter', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'ResponseCapability.firefighter_emt'
        db.alter_column(u'firestation_responsecapability', 'firefighter_emt', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'ResponseCapability.chief_officer'
        db.alter_column(u'firestation_responsecapability', 'chief_officer', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'ResponseCapability.firefighter_paramedic'
        db.alter_column(u'firestation_responsecapability', 'firefighter_paramedic', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'ResponseCapability.ems_emt'
        db.alter_column(u'firestation_responsecapability', 'ems_emt', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'ResponseCapability.ems_paramedic'
        db.alter_column(u'firestation_responsecapability', 'ems_paramedic', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'ResponseCapability.officer'
        db.alter_column(u'firestation_responsecapability', 'officer', self.gf('django.db.models.fields.IntegerField')(null=True))

    models = {
        u'firestation.firecaresbase': {
            'Meta': {'object_name': 'FireCaresBase'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'firestation.firestation': {
            'Meta': {'ordering': "('state', 'city', 'name')", 'object_name': 'FireStation', '_ormbases': [u'firestation.USGSStructureData', u'firestation.FireCaresBase']},
            'district': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'fips': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'firecaresbase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['firestation.FireCaresBase']", 'unique': 'True'}),
            'jurisdiction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['firestation.Jurisdiction']", 'null': 'True', 'blank': 'True'}),
            'station_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'usgsstructuredata_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['firestation.USGSStructureData']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'firestation.jurisdiction': {
            'Meta': {'ordering': "('state_name', 'county_name')", 'object_name': 'Jurisdiction', '_ormbases': [u'firestation.FireCaresBase']},
            'county_fipscode': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'county_name': ('django.db.models.fields.CharField', [], {'max_length': '120', 'null': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'fips': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'firecaresbase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['firestation.FireCaresBase']", 'unique': 'True', 'primary_key': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
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
        u'firestation.responsecapability': {
            'Meta': {'object_name': 'ResponseCapability', '_ormbases': [u'firestation.FireCaresBase']},
            'apparatus': ('django.db.models.fields.CharField', [], {'default': "'Engine'", 'max_length': '20'}),
            'chief_officer': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'ems_emt': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'ems_paramedic': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'ems_supervisor': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            u'firecaresbase_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['firestation.FireCaresBase']", 'unique': 'True', 'primary_key': 'True'}),
            'firefighter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'firefighter_emt': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'firefighter_paramedic': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'firestation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['firestation.FireStation']"}),
            'officer': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'officer_paramedic': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'})
        },
        u'firestation.usgsstructuredata': {
            'Meta': {'ordering': "('state', 'city', 'name')", 'object_name': 'USGSStructureData'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'addressbuildingname': ('django.db.models.fields.CharField', [], {'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'admintype': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'complex_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'data_security': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'distribution_policy': ('django.db.models.fields.CharField', [], {'max_length': '4', 'null': 'True', 'blank': 'True'}),
            'fcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'foot_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'ftype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'globalid': ('django.db.models.fields.CharField', [], {'max_length': '38', 'null': 'True', 'blank': 'True'}),
            'gnis_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'islandmark': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'loaddate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'objectid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'permanent_identifier': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'pointlocationtype': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_datadesc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'source_datasetid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_featureid': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'source_originator': ('django.db.models.fields.CharField', [], {'max_length': '130', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['firestation']