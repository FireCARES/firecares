# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Country'
        db.create_table(u'firecares_core_country', (
            ('iso_code', self.gf('django.db.models.fields.CharField')(max_length=2, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=45)),
        ))
        db.send_create_signal(u'firecares_core', ['Country'])

        # Adding model 'Address'
        db.create_table(u'firecares_core_address', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address_line1', self.gf('django.db.models.fields.CharField')(max_length=45)),
            ('address_line2', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('state_province', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['firecares_core.Country'])),
            ('geom', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'firecares_core', ['Address'])

        # Adding unique constraint on 'Address', fields ['address_line1', 'address_line2', 'postal_code', 'city', 'state_province', 'country']
        db.create_unique(u'firecares_core_address', ['address_line1', 'address_line2', 'postal_code', 'city', 'state_province', 'country_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Address', fields ['address_line1', 'address_line2', 'postal_code', 'city', 'state_province', 'country']
        db.delete_unique(u'firecares_core_address', ['address_line1', 'address_line2', 'postal_code', 'city', 'state_province', 'country_id'])

        # Deleting model 'Country'
        db.delete_table(u'firecares_core_country')

        # Deleting model 'Address'
        db.delete_table(u'firecares_core_address')


    models = {
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
        }
    }

    complete_apps = ['firecares_core']