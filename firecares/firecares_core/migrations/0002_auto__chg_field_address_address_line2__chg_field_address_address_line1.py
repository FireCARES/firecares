# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Address.address_line2'
        db.alter_column(u'firecares_core_address', 'address_line2', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'Address.address_line1'
        db.alter_column(u'firecares_core_address', 'address_line1', self.gf('django.db.models.fields.CharField')(max_length=100))

    def backwards(self, orm):

        # Changing field 'Address.address_line2'
        db.alter_column(u'firecares_core_address', 'address_line2', self.gf('django.db.models.fields.CharField')(max_length=45))

        # Changing field 'Address.address_line1'
        db.alter_column(u'firecares_core_address', 'address_line1', self.gf('django.db.models.fields.CharField')(max_length=45))

    models = {
        u'firecares_core.address': {
            'Meta': {'unique_together': "(('address_line1', 'address_line2', 'postal_code', 'city', 'state_province', 'country'),)", 'object_name': 'Address'},
            'address_line1': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'address_line2': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
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
        }
    }

    complete_apps = ['firecares_core']