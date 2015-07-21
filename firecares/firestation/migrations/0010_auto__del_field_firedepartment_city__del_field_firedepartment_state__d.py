# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'FireDepartment.city'
        db.delete_column(u'firestation_firedepartment', 'city')

        # Deleting field 'FireDepartment.state'
        db.delete_column(u'firestation_firedepartment', 'state')

        # Deleting field 'FireDepartment.street_address'
        db.delete_column(u'firestation_firedepartment', 'street_address')

        # Adding field 'FireDepartment.headquarters_address'
        db.add_column(u'firestation_firedepartment', 'headquarters_address',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='firedepartment_headquarters', null=True, to=orm['firecares_core.Address']),
                      keep_default=False)

        # Adding field 'FireDepartment.mail_address'
        db.add_column(u'firestation_firedepartment', 'mail_address',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['firecares_core.Address'], null=True, blank=True),
                      keep_default=False)

        # Adding field 'FireDepartment.headquarters_phone'
        db.add_column(u'firestation_firedepartment', 'headquarters_phone',
                      self.gf('phonenumber_field.modelfields.PhoneNumberField')(max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FireDepartment.headquarters_fax'
        db.add_column(u'firestation_firedepartment', 'headquarters_fax',
                      self.gf('phonenumber_field.modelfields.PhoneNumberField')(max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FireDepartment.department_type'
        db.add_column(u'firestation_firedepartment', 'department_type',
                      self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FireDepartment.organization_type'
        db.add_column(u'firestation_firedepartment', 'organization_type',
                      self.gf('django.db.models.fields.CharField')(max_length=75, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FireDepartment.website'
        db.add_column(u'firestation_firedepartment', 'website',
                      self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'FireDepartment.city'
        db.add_column(u'firestation_firedepartment', 'city',
                      self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'FireDepartment.state'
        raise RuntimeError("Cannot reverse this migration. 'FireDepartment.state' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'FireDepartment.state'
        db.add_column(u'firestation_firedepartment', 'state',
                      self.gf('django.db.models.fields.CharField')(max_length=2),
                      keep_default=False)

        # Adding field 'FireDepartment.street_address'
        db.add_column(u'firestation_firedepartment', 'street_address',
                      self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True),
                      keep_default=False)

        # Deleting field 'FireDepartment.headquarters_address'
        db.delete_column(u'firestation_firedepartment', 'headquarters_address_id')

        # Deleting field 'FireDepartment.mail_address'
        db.delete_column(u'firestation_firedepartment', 'mail_address_id')

        # Deleting field 'FireDepartment.headquarters_phone'
        db.delete_column(u'firestation_firedepartment', 'headquarters_phone')

        # Deleting field 'FireDepartment.headquarters_fax'
        db.delete_column(u'firestation_firedepartment', 'headquarters_fax')

        # Deleting field 'FireDepartment.department_type'
        db.delete_column(u'firestation_firedepartment', 'department_type')

        # Deleting field 'FireDepartment.organization_type'
        db.delete_column(u'firestation_firedepartment', 'organization_type')

        # Deleting field 'FireDepartment.website'
        db.delete_column(u'firestation_firedepartment', 'website')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'firecares_core.address': {
            'Meta': {'unique_together': "(('address_line1', 'address_line2', 'postal_code', 'city', 'state_province', 'country'),)", 'object_name': 'Address'},
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '45'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['firecares_core.Country']"}),
            'geom': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'state_province': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        },
        u'firecares_core.country': {
            'Meta': {'ordering': "['name', 'iso_code']", 'object_name': 'Country'},
            'iso_code': ('django.db.models.fields.CharField', [], {'max_length': '2', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '45'})
        },
        u'firestation.firedepartment': {
            'Meta': {'object_name': 'FireDepartment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'department_type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'fdid': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'geom': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'headquarters_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'firedepartment_headquarters'", 'null': 'True', 'to': u"orm['firecares_core.Address']"}),
            'headquarters_fax': ('phonenumber_field.modelfields.PhoneNumberField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'headquarters_phone': ('phonenumber_field.modelfields.PhoneNumberField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mail_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['firecares_core.Address']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'organization_type': ('django.db.models.fields.CharField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'firestation.firestation': {
            'Meta': {'ordering': "('state', 'city', 'name')", 'object_name': 'FireStation', '_ormbases': [u'firestation.USGSStructureData']},
            'department': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['firestation.FireDepartment']", 'null': 'True', 'blank': 'True'}),
            'district': ('django.contrib.gis.db.models.fields.PolygonField', [], {'null': 'True', 'blank': 'True'}),
            'fdid': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
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