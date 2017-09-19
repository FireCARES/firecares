import datetime
import json
import requests
import sys
import us

from django.conf import settings
from django.db import connections
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, MultiPolygon
from django.contrib.gis.geos import LinearRing, Polygon
from django.contrib.gis.measure import D
from django.db.transaction import rollback
from django.db.utils import IntegrityError
from django.core.serializers import serialize

from firecares.firestation.models import FireStation, FireDepartment

from reversion import revisions as reversion


WEATHER_WARNING_SOURCE = [('deafult', 'default-provider')]


class WeatherWarnings(models.Model):
    """
    Weather Warnings from NOAA.
    """
    service_id_warnings = 0 #no data
    service_id_watches = 1 

    prod_type = models.CharField(max_length=200, null=True, blank=True)
    oid = models.CharField(max_length=38, null=True, blank=True)
    idp_source = models.CharField(max_length=200, null=True, blank=True)
    idp_subset = models.CharField(max_length=200, null=True, blank=True)
    url = models.CharField(max_length=500, null=True, blank=True)
    event = models.CharField(max_length=200, null=True, blank=True)
    wfo = models.CharField(max_length=200, null=True, blank=True)
    warnid = models.CharField(max_length=200, null=True, blank=True)
    phenom = models.CharField(max_length=200, null=True, blank=True)
    sig = models.CharField(max_length=200, null=True, blank=True)
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


class DepartmentWarnings(models.Model):

    #For warnings related to departments
    departmentfdid = models.CharField(max_length=10, blank=True)
    departmentname = models.CharField(max_length=100)
    warningfdid = models.CharField(max_length=10, blank=True)
    warningname = models.CharField(max_length=200)
    prod_type = models.CharField(max_length=100, null=True, blank=True)
    expiredate = models.DateTimeField(null=True, blank=True)
    issuedate = models.DateTimeField(null=True, blank=True)
    warngeom = models.MultiPolygonField()

class StationWarnings(models.Model):

    #For warnings related to stations
    stationfdid = models.CharField(max_length=10, blank=True)
    stationname = models.CharField(max_length=200)
    warningfdid = models.CharField(max_length=10, blank=True)
    prod_type = models.CharField(max_length=200, null=True, blank=True)
    warningname = models.CharField(max_length=200)
    expiredate = models.DateTimeField(null=True, blank=True)
    issuedate = models.DateTimeField(null=True, blank=True)
    warngeom = models.MultiPolygonField()



reversion.register(WeatherWarnings)
reversion.register(StationWarnings)
reversion.register(DepartmentWarnings)
