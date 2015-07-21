# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'ResponseCapability'
        db.delete_table(u'firestation_responsecapability')

        # Adding model 'Staffing'
        db.create_table(u'firestation_staffing', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('firestation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['firestation.FireStation'])),
            ('apparatus', self.gf('django.db.models.fields.CharField')(default='Engine', max_length=20)),
            ('firefighter', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('firefighter_emt', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('firefighter_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('ems_emt', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('ems_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('officer', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('officer_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('ems_supervisor', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('chief_officer', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
        ))
        db.send_create_signal(u'firestation', ['Staffing'])


    def backwards(self, orm):
        # Adding model 'ResponseCapability'
        db.create_table(u'firestation_responsecapability', (
            ('ems_supervisor', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('firefighter_emt', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('chief_officer', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('firefighter_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('officer_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('firestation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['firestation.FireStation'])),
            ('apparatus', self.gf('django.db.models.fields.CharField')(default='Engine', max_length=20)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('firefighter', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('ems_emt', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('ems_paramedic', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
            ('officer', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=2, null=True, blank=True)),
        ))
        db.send_create_signal(u'firestation', ['ResponseCapability'])

        # Deleting model 'Staffing'
        db.delete_table(u'firestation_staffing')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'firestation.firedepartment': {
            'Meta': {'object_name': 'FireDepartment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'fips': ('django.db.models.fields.CharField', [], {'max_length': '10', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        u'firestation.firestation': {
            'Meta': {'ordering': "('state', 'city', 'name')", 'object_name': 'FireStation', '_ormbases': [u'firestation.USGSStructureData']},
            'department': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['firestation.FireDepartment']", 'null': 'True', 'blank': 'True'}),
            'district': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'fips': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'station_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'usgsstructuredata_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['firestation.USGSStructureData']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'firestation.staffing': {
            'Meta': {'object_name': 'Staffing'},
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