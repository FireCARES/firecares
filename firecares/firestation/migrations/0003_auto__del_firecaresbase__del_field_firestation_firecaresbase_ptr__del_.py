# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'FireCaresBase'
        db.delete_table(u'firestation_firecaresbase')

        # Deleting field 'FireStation.firecaresbase_ptr'
        db.delete_column(u'firestation_firestation', u'firecaresbase_ptr_id')

        # Deleting field 'ResponseCapability.firecaresbase_ptr'
        db.delete_column(u'firestation_responsecapability', u'firecaresbase_ptr_id')


        # Adding field 'ResponseCapability.id'
        #db.add_column(u'firestation_responsecapability', u'id',
        #              self.gf('django.db.models.fields.IntegerField')(primary_key=True),
        #              keep_default=False)

        #db.execute("CREATE SEQUENCE firestation_responsecapability_id_seq")
        #db.execute("SELECT setval('firestation_responsecapability_id_seq', (SELECT MAX(id) FROM firestation_responsecapability))")
        #db.execute("ALTER TABLE firestation_jurisdiction ALTER COLUMN id SET DEFAULT nextval('firestation_jurisdiction_id_seq'::regclass)")


        # Adding field 'ResponseCapability.created'
        db.add_column(u'firestation_responsecapability', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2015, 2, 27, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'ResponseCapability.modified'
        db.add_column(u'firestation_responsecapability', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(2015, 2, 27, 0, 0), blank=True),
                      keep_default=False)

        # Deleting field 'Jurisdiction.firecaresbase_ptr'
        db.delete_column(u'firestation_jurisdiction', u'firecaresbase_ptr_id')

        # Adding field 'Jurisdiction.id'
        #db.add_column(u'firestation_jurisdiction', u'id',
        #              self.gf('django.db.models.fields.AutoField')(primary_key=True),
        #              keep_default=False)

        # Adding field 'Jurisdiction.created'
        db.add_column(u'firestation_jurisdiction', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2015, 2, 27, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'Jurisdiction.modified'
        db.add_column(u'firestation_jurisdiction', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(2015, 2, 27, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'USGSStructureData.created'
        db.add_column(u'firestation_usgsstructuredata', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2015, 2, 27, 0, 0), blank=True),
                      keep_default=False)

        # Adding field 'USGSStructureData.modified'
        db.add_column(u'firestation_usgsstructuredata', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.datetime(2015, 2, 27, 0, 0), blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'FireCaresBase'
        db.create_table(u'firestation_firecaresbase', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'firestation', ['FireCaresBase'])


        # User chose to not deal with backwards NULL issues for 'FireStation.firecaresbase_ptr'
        raise RuntimeError("Cannot reverse this migration. 'FireStation.firecaresbase_ptr' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'FireStation.firecaresbase_ptr'
        db.add_column(u'firestation_firestation', u'firecaresbase_ptr',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['firestation.FireCaresBase'], unique=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'ResponseCapability.firecaresbase_ptr'
        raise RuntimeError("Cannot reverse this migration. 'ResponseCapability.firecaresbase_ptr' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'ResponseCapability.firecaresbase_ptr'
        db.add_column(u'firestation_responsecapability', u'firecaresbase_ptr',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['firestation.FireCaresBase'], unique=True, primary_key=True),
                      keep_default=False)

        # Deleting field 'ResponseCapability.id'
        db.delete_column(u'firestation_responsecapability', u'id')

        # Deleting field 'ResponseCapability.created'
        db.delete_column(u'firestation_responsecapability', 'created')

        # Deleting field 'ResponseCapability.modified'
        db.delete_column(u'firestation_responsecapability', 'modified')


        # User chose to not deal with backwards NULL issues for 'Jurisdiction.firecaresbase_ptr'
        raise RuntimeError("Cannot reverse this migration. 'Jurisdiction.firecaresbase_ptr' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'Jurisdiction.firecaresbase_ptr'
        db.add_column(u'firestation_jurisdiction', u'firecaresbase_ptr',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['firestation.FireCaresBase'], unique=True, primary_key=True),
                      keep_default=False)

        # Deleting field 'Jurisdiction.id'
        db.delete_column(u'firestation_jurisdiction', u'id')

        # Deleting field 'Jurisdiction.created'
        db.delete_column(u'firestation_jurisdiction', 'created')

        # Deleting field 'Jurisdiction.modified'
        db.delete_column(u'firestation_jurisdiction', 'modified')

        # Deleting field 'USGSStructureData.created'
        db.delete_column(u'firestation_usgsstructuredata', 'created')

        # Deleting field 'USGSStructureData.modified'
        db.delete_column(u'firestation_usgsstructuredata', 'modified')


    models = {
        u'firestation.firestation': {
            'Meta': {'ordering': "('state', 'city', 'name')", 'object_name': 'FireStation', '_ormbases': [u'firestation.USGSStructureData']},
            'district': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'fips': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'jurisdiction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['firestation.Jurisdiction']", 'null': 'True', 'blank': 'True'}),
            'station_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'usgsstructuredata_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['firestation.USGSStructureData']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'firestation.jurisdiction': {
            'Meta': {'ordering': "('state_name', 'county_name')", 'object_name': 'Jurisdiction'},
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
        u'firestation.responsecapability': {
            'Meta': {'object_name': 'ResponseCapability'},
            'apparatus': ('django.db.models.fields.CharField', [], {'default': "'Engine'", 'max_length': '20'}),
            'chief_officer': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ems_emt': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'ems_paramedic': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'ems_supervisor': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'firefighter': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'firefighter_emt': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'firefighter_paramedic': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'firestation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['firestation.FireStation']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
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
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
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
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
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