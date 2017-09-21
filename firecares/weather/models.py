from dateutil.parser import parse as date_parse
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
from django.contrib.gis.geos import fromstr
from django.contrib.gis.measure import D
from django.db.transaction import rollback
from django.db.utils import IntegrityError
from django.core.serializers import serialize

from firecares.firestation.models import FireStation, FireDepartment

from reversion import revisions as reversion


WEATHER_WARNING_SOURCE = [('deafult', 'default-provider')]


class WeatherWarnings(models.Model):
    """
    Weather Warnings from NOAA
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
    warnid = models.CharField(max_length=200, null=False, blank=True)
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
        This object's URI (from the NOAA map service )

        #2017-09-18T01:00:00+00:00 time format
        
        """
        return 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/{0}?f=json' \
            .format(self.objectid)

    @classmethod
    def load_warning_data(cls):

        objects = requests.get('https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/query?'
                  'where=1=1&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false'
                  '&returnTrueCurves=false&outSR=&returnIdsOnly=true&returnCountOnly=false&returnZ=false&returnM=false&returnDistinctValues=false&f=json', timeout=20)


        print objects.content  #sometimes error/empty 

        object_ids = set(json.loads(objects.content)['objectIds'])

        url = 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/{0}?f=json'
        
        for object in object_ids:

            try:

              obj = requests.get(url.format(object), timeout=20 )
              obj = json.loads(obj.content)

              data = dict((k.lower(), v) for k, v in obj['feature']['attributes'].iteritems())
              warninggeom = ''; 
              datapost = {}
              
              #Check if warning is already loaded and update as needed
              if WeatherWarnings.objects.filter(warnid=data['warnid']):

                  datapost = WeatherWarnings.objects.filter(warnid=data['warnid'])
                  
                  warningfeature = datapost[0]
                  
                  if data['expiration'] != " ":
                      warningfeature.expiration = date_parse(data['expiration'])

                  if obj['feature'].get('geometry'):
                      poly = map(LinearRing, obj['feature']['geometry']['rings'])
                      warningfeature.warngeom = MultiPolygon(fromstr(str(Polygon(*poly))),)  # not sure if data is multi poly
                      warninggeom = MultiPolygon(fromstr(str(Polygon(*poly))),)

                  warningfeature.issuance = date_parse(data['issuance']) 
                  warningfeature.idp_subset = data['idp_subset'] 

                  print data['warnid'] + " Updated"

              else:

                  datapost['prod_type'] = data['prod_type'] 
                  datapost['idp_source'] = data['idp_source'] 
                  datapost['sig'] = data['sig']
                  datapost['wfo'] = data['wfo'] 
                  datapost['url'] = data['url'] 
                  datapost['phenom'] = data['phenom']  
                  
                  if data['expiration'] != " ":
                      datapost['expiration'] = date_parse(data['issuance'])

                  if obj['feature'].get('geometry'):
                      poly = map(LinearRing, obj['feature']['geometry']['rings'])
                      datapost['warngeom'] = MultiPolygon(fromstr(str(Polygon(*poly))),)  # not sure if data is multi poly
                      warninggeom = MultiPolygon(fromstr(str(Polygon(*poly))),)

                  datapost['issuance'] = date_parse(data['issuance']) #datetime.datetime.strptime(data['issuance'].split('+')[0], '%Y-%m-%dT%H:%M:%S')
                  
                  datapost['idp_subset'] = data['idp_subset'] 
                  datapost['warnid'] = data['warnid'] 

                  warningfeature = cls.objects.create(**datapost)
                  print 'Created Warning: {0}'.format(data.get('warnid'))


              warningfeature.save()

              #Intersect with Departments and update table if overlap
              if(warninggeom != ''):

                  intersectDepartmentList = FireDepartment.objects.filter(geom__intersects=warninggeom)

                  if(intersectDepartmentList.count()> 0):

                      WeatherWarnings.add_warnings_to_departments(intersectDepartmentList, warningfeature)
                      print "Total intersecting Departments " + str(intersectDepartmentList.count())

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


        print '{0} Total Weather Warnings.'.format(WeatherWarnings.objects.all().count())

    @classmethod
    def add_warnings_to_departments(self, departmentQuerySet, weatherWarnings):
        """
        adds and updates departement weather warnings
        """

        for fireDept in departmentQuerySet:

            try:

                print(weatherWarnings.prod_type + " for " + fireDept.name)
                print("Warning Expires " + str(weatherWarnings.expiration.strftime('%c')))

                #Check if warning is already loaded and update as needed
                if DepartmentWarnings.objects.filter(warningfdid=weatherWarnings.warnid, departmentfdid=fireDept.fdid):

                    dataduplicate = DepartmentWarnings.objects.filter(warningfdid=weatherWarnings.warnid, departmentfdid=fireDept.fdid)
                    
                    deptupdate = dataduplicate[0]

                    deptupdate.warningname = weatherWarnings.prod_type
                    deptupdate.prod_type = weatherWarnings.prod_type
                    deptupdate.expiredate = weatherWarnings.expiration
                    deptupdate.issuedate = weatherWarnings.issuance
                    deptupdate.url = weatherWarnings.url
                    deptupdate.warngeom = weatherWarnings.warngeom

                    deptupdate.save()

                    print 'Department Warning Updated'

                else:

                    dataadd = {}

                    dataadd['departmentfdid'] = fireDept.fdid
                    dataadd['departmentname'] = fireDept.name
                    dataadd['warningfdid'] = weatherWarnings.warnid
                    dataadd['warningname'] = weatherWarnings.prod_type
                    dataadd['prod_type'] = weatherWarnings.prod_type
                    dataadd['expiredate'] = weatherWarnings.expiration
                    dataadd['issuedate'] = weatherWarnings.issuance
                    dataadd['url'] = weatherWarnings.url
                    dataadd['warngeom'] = weatherWarnings.warngeom

                    deptupdate = DepartmentWarnings.objects.create(**dataadd)
                    deptupdate.save()

                    print 'Department Warning Created'

            except:
                
                print 'Error running Department Query'
                return
    
    @property
    def warning_area(self):
        """
        Project data as needed
        """
        if self.district:
            try:
                return (self.warngeom.transform(102009, clone=True).area / 1000000) * 0.38610
            except:
                return

    class Meta:
        verbose_name = 'Weather Warnings'


class DepartmentWarnings(models.Model):

    #For warnings related to departments
    departmentfdid = models.CharField(max_length=10, blank=True)
    departmentname = models.CharField(max_length=100)
    warningfdid = models.CharField(max_length=100, blank=True)
    warningname = models.CharField(max_length=200)
    prod_type = models.CharField(max_length=100, null=True, blank=True)
    expiredate = models.DateTimeField(null=True, blank=True)
    issuedate = models.DateTimeField(null=True, blank=True)
    url = models.CharField(max_length=500, null=True, blank=True)
    warngeom = models.MultiPolygonField()


    @classmethod
    def create_dept_warning(cls, departmentarning, **kwargs):
        """
        Create Departement warnings.
        """

        deptwarn = DepartmentWarnings(departmentfdid=departmentarning.departmentfdid,
                                      departmentname=departmentarning.departmentname,
                                      warningfdid=departmentarning.warningfdid,
                                      warningname=departmentarning.warningname,
                                      url=departmentarning.url,
                                      prod_type=departmentarning.prod_type,
                                      warngeom=departmentarning.warngeom,
                                      issuedate=departmentarning.issuedate,
                                      expiration=departmentarning.expiration,
                                      **kwargs)

        deptwarn.save()
        return deptwarn


reversion.register(WeatherWarnings)
reversion.register(DepartmentWarnings)
