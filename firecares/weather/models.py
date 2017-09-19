import datetime
import json
import requests
import sys
import us

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, MultiPolygon
from django.contrib.gis.geos import LinearRing, Polygon
from django.contrib.gis.measure import D
from django.db.transaction import rollback
from django.db.utils import IntegrityError
from django.core.serializers import serialize

from reversion import revisions as reversion

DATA_SECURITY_CHOICES = [(0, 'Unknown'),
                         (1, 'Top Secret'),
                         (2, 'Secret'),
                         (3, 'Confidential'),
                         (4, 'Restricted'),
                         (5, 'Unclassified'),
                         (6, 'Sensitive')]

DISTRIBUTION_POLICY_CHOICES = [('A1', 'Emergency Service Provider - Internal Use Only'),
                               ('A2', 'Emergency Service Provider - Bitmap Display Via Web'),
                               ('A3', 'Emergency Service Provider - Free Distribution to Third Parties'),
                               ('A4', 'Emergency Service Provider - Free Distribution to Third Parties Via'
                                      ' Internet'),
                               ('B1', 'Government Agencies or Their Delegated Agents - Internal Use Only'),
                               ('B2', 'Government Agencies or Their Delegated Agents - Bitmap Display Via Web'),
                               ('B3', 'Government Agencies or Their Delegated Agents - Free Distribution to Third'
                                      ' Parties'),
                               ('B4', 'Government Agencies or Their Delegated Agents - Free Distribution to Third'
                                      ' Parties Via Internet'),
                               ('C1', 'Other Public or Educational Institutions - Internal Use Only'),
                               ('C2', 'Other Public or Educational Institutions - Bitmap Display Via Web'),
                               ('C3', 'Other Public or Educational Institutions - Free Distribution to Third'
                                      ' Parties'),
                               ('C4', 'Other Public or Educational Institutions - Free Distribution to Third'
                                      ' Parties Via Internet'),
                               ('D1', 'Data Contributors - Internal Use Only'), ('D2', 'Data Contributors - '
                                                                                       'Bitmap Display Via Web'),
                               ('D3', 'Data Contributors - Free Distribution to Third Parties'),
                               ('D4', 'Data Contributors - Free Distribution to Third Parties Via Internet'),
                               ('E1', 'Public Domain - Internal Use Only'), ('E2', 'Public Domain - Bitmap'
                                                                                   ' Display Via Web'),
                               ('E3', 'Public Domain - Free Distribution to Third Parties'),
                               ('E4', 'Public Domain - Free Distribution to Third Parties Via Internet')]


class WeatherWarnings(models.Model):
    """
    Weather Warnings from NOAA.
    """
    service_id_warnings = 0 #no data
    service_id_watches = 1 

    prod_type = models.CharField(max_length=30, null=True, blank=True)
    oid = models.CharField(max_length=38, null=True, blank=True)
    idp_source = models.CharField(max_length=38, null=True, blank=True)
    idp_subset = models.CharField(max_length=38, null=True, blank=True)
    url = models.CharField(max_length=38, null=True, blank=True)
    event = models.CharField(max_length=38, null=True, blank=True)
    wfo = models.CharField(max_length=38, null=True, blank=True)
    warnid = models.CharField(max_length=38, null=True, blank=True)
    phenom = models.CharField(max_length=38, null=True, blank=True)
    sig = models.CharField(max_length=38, null=True, blank=True)
    expiration = models.DateTimeField(null=True, blank=True)
    idp_ingestdate = models.DateTimeField(null=True, blank=True)
    issuance = models.DateTimeField(null=True, blank=True)
    warngeom = models.MultiPolygonField()


    @classmethod
    def create_warning(cls, warning, **kwargs):
        """
        create warnings.
        """

        warn = WeatherWarnings(prod_type=warning.prod_type,
                              idp_source=warning.idp_source,
                              event=warning.event,
                              phenom=warning.phenom,
                              url=warning.url,
                              issuance=warning.issuance,
                              warngeom=warning.warngeom,
                              idp_subset=warning.idp_subset,
                              warnid=warning.warnid,
                              expiration=warning.expiration,
                              **kwargs)

        warn.save()
        return warn


    @property
    def origin_uri(self):
        """
        This object's URI (from the national map).
        """
        return 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/{0}?f=json' \
            .format(self.objectid)

    @classmethod
    def load_data(cls):
        objects = requests.get('https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/query?'
            'where=1=1&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false'
            '&returnTrueCurves=false&outSR=&returnIdsOnly=true&returnCountOnly=false&returnZ=false&returnM=false&returnDistinctValues=false&'
            'false&parameterValues=&rangeValues=&f=json')

        current_ids = set(WeatherWarnings.objects.all().values_list('objectid', flat=True))
        object_ids = set(json.loads(objects.content)['objectIds']) - current_ids
        url = 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/{0}?f=json'
        
        for object in object_ids:
            try:

                if WeatherWarnings.objects.filter(objectid=object):
                    continue

                obj = requests.get(url.format(object))
                obj = json.loads(obj.content)
                data = dict((k.lower(), v) for k, v in obj['feature']['attributes'].iteritems())

                if obj['feature'].get('geometry'):
                    poly = map(LinearRing, obj['feature']['geometry']['rings'])
                    data['warngeom'] = Polygon(*poly)

                data['prod_type'] = data['prod_type'] 
                data['idp_source'] = data['prod_type'] 
                data['phenom'] = data['phenom'] 
                
                #2017-09-18T01:00:00+00:00
                data['issuance'] = datetime.strptime(data['issuance'], '%Y-%d-%dT%H-%M-%S+00:00')
                data['expiration'] = datetime.strptime(data['expiration'], '%Y-%d-%dT%H-%M-%S+00:00')

                data['idp_subset'] = data['idp_subset'] 
                data['warnid'] = data['warnid'] 

                feat = cls.objects.create(**data)
                feat.save()

                print 'Saved object: {0}'.format(data.get('name'))
                print '{0} Weather Warning loaded.'.format(WeatherWarnings.objects.all().count())

            except KeyError:
                print '{0} failed.'.format(object)
                print url.format(object)

            except IntegrityError:
                print '{0} failed.'.format(object)
                print url.format(object)
                print sys.exc_info()

                try:
                    rollback()
                except:
                    pass

            except:
                print '{0} failed.'.format(object)
                print url.format(object)
                print sys.exc_info()

    @property
    def warning_area(self):
        """
        Project the district's geometry into US National Atlas Equal Area
        Returns mi2
        """
        if self.district:
            try:
                return (self.district.transform(102009, clone=True).area / 1000000) * 0.38610
            except:
                return

    class Meta:
        verbose_name = 'Weather Warnings'


class WarningData(WeatherWarnings):

    #For additional warnings sources
    warning_url = models.CharField(max_length=320, null=True, blank=True)
    warning_vendor = models.CharField(max_length=120, null=True, blank=True)
    warning_type = models.CharField(max_length=120, null=True, blank=True)
    objectid = models.IntegerField(null=True, blank=True, unique=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    admintype = models.IntegerField(choices=ownerclass_domain, null=True, blank=True)
    geom = models.MultiPolygonField()


reversion.register(WeatherWarnings)
