import datetime
import json
import requests
import sys
import us

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import MaxValueValidator
from django.core.urlresolvers import reverse
from django.db.transaction import rollback
from django.db.utils import IntegrityError

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


class USGSBase(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    permanent_identifier = models.CharField(max_length=40, null=True, blank=True)
    source_featureid = models.CharField(max_length=40, null=True, blank=True)
    source_datasetid = models.CharField(max_length=40, null=True, blank=True)
    source_datadesc = models.CharField(max_length=100, null=True, blank=True)
    source_originator = models.CharField(max_length=130, null=True, blank=True)
    data_security = models.IntegerField(blank=True, null=True, choices=DATA_SECURITY_CHOICES)
    distribution_policy = models.CharField(max_length=4, choices=DISTRIBUTION_POLICY_CHOICES, null=True, blank=True)
    loaddate = models.DateTimeField(null=True, blank=True)
    ftype = models.CharField(blank=True, null=True, max_length=50)
    gnis_id = models.CharField(max_length=10, null=True, blank=True)
    globalid = models.CharField(max_length=38, null=True, blank=True)
    objects = models.GeoManager()

    class Meta:
        abstract = True

    @classmethod
    def count_differential(cls):
        """
        Reports the count differential between the upstream service and this table.
        """
        url = 'http://services.nationalmap.gov/arcgis/rest/services/govunits/MapServer/{0}/query?' \
              'where=1%3D1&text=&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&' \
              'spatialRel=esriSpatialRelIntersects&relationParam=&outFields=&returnGeometry=true' \
              '&maxAllowableOffset=&geometryPrecision=&outSR=&returnIdsOnly=false&returnCountOnly=true&orderByFields=' \
              '&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&gdbVersion=&' \
              'returnDistinctValues=false&f=pjson'

        response = requests.get(url.format(cls.service_id))

        if response.ok:
            response_js = json.loads(response.content)
            upstream_count = response_js.get('count')

            if upstream_count:
                local_count = cls.objects.all().count()
                print 'The upstream service has: {0} features.'.format(upstream_count)
                print 'The local model {1} has: {0} features.'.format(local_count, cls.__name__)
                return local_count - upstream_count


    @classmethod
    def load_data(cls):
        # Still need to load from jurisdictions
        from django.contrib.gis.geos import LinearRing, Polygon
        endpoint = cls.service_id
        objects = requests.get('http://services.nationalmap.gov/arcgis/rest/services/govunits/MapServer/{0}/query?'
                               'where=1%3D1&text=&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&'
                               'spatialRel=esriSpatialRelIntersects&relationParam=&outFields=&returnGeometry=true&'
                               'maxAllowableOffset=&geometryPrecision=&outSR=&returnIdsOnly=true&returnCountOnly=false&'
                               'orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&'
                               'gdbVersion=&returnDistinctValues=false&f=json'.format(endpoint))

        current_ids = set(cls.objects.all().values_list('objectid', flat=True))
        object_ids = set(json.loads(objects.content)['objectIds']) - current_ids
        url = 'http://services.nationalmap.gov/arcgis/rest/services/govunits/MapServer/{1}/{0}?f=json'

        for object in object_ids:
            try:

                if cls.objects.filter(objectid=object):
                    continue

                obj = requests.get(url.format(object, endpoint))
                obj = json.loads(obj.content)
                data = dict((k.lower(), v) for k, v in obj['feature']['attributes'].iteritems())

                for key in data.keys():
                    if key not in [field.name for field in cls._meta.fields]:
                        data.pop(key)

                if obj['feature'].get('geometry'):
                    poly = map(LinearRing, obj['feature']['geometry']['rings'])
                    data['geom'] = Polygon(*poly)

                data['loaddate'] = datetime.datetime.fromtimestamp(data['loaddate']/1000.0)
                feat = cls.objects.create(**data)
                feat.save()
                print 'Saved object: {0}'.format(data.get('name'))
                print '{0} {1} loaded.'.format(cls.objects.all().count(), cls._meta.verbose_name_plural)

            except KeyError:
                print '{0} failed.'.format(object)
                print url.format(object, endpoint)

            except IntegrityError:
                print '{0} failed.'.format(object)
                print url.format(object, endpoint)
                print sys.exc_info()

                try:
                    rollback()
                except:
                    pass

            except:
                print '{0} failed.'.format(object)
                print url.format(object, endpoint)
                print sys.exc_info()



class Reserve(USGSBase):
    service_id = 11
    wilderness_fcode_1 = [(67500, u'Wilderness')]
    ownerclass_domain = [(0, u'Unknown'), (1, u'Federal'), (2, u'Tribal'), (3, u'State'), (4, u'Regional'), (5, u'County'), (6, u'Municipal'), (7, u'Private')]
    ownerormanagingagency_domain = [(1, u'Army Corps of Engineers'), (15, u'Bureau of Census'), (2, u'Bureau of Indian Affairs'), (3, u'Bureau of Land Management'), (4, u'Bureau of Reclamation'), (5, u'Department of Defense'), (6, u'Department of Energy'), (7, u'Department of Homeland Security'), (8, u'Department of Transportation'), (9, u'Department of Veteran Affairs'), (10, u'Fish and Wildlife Service'), (11, u'Forest Service'), (12, u'National Oceanic and Atmospheric Administration'), (13, u'National Park Service'), (14, u'Tennessee Valley Authority'), (99, u'Not Applicable')]
    objectid = models.IntegerField(null=True, blank=True, unique=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    fcode = models.IntegerField(choices=wilderness_fcode_1, null=True, blank=True)
    admintype = models.IntegerField(choices=ownerclass_domain, null=True, blank=True)
    ownerormanagingagency = models.IntegerField(choices=ownerormanagingagency_domain, null=True, blank=True)
    geom = models.PolygonField()


class NativeAmericanArea(USGSBase):
    service_id = 12
    nativeamericanreservation_fcode = [(64000, u'Native American Reservation'), (64080, u'Tribal Designated Statistic Area'), (64081, u'Colony'), (64082, u'Community'), (64083, u'Joint Use Area'), (64084, u'Pueblo'), (64085, u'Rancheria'), (64086, u'Reservation'), (64087, u'Reserve'), (64088, u'Oklahoma Tribal Statistical Area'), (64089, u'American Indian Trust Land'), (64090, u'Joint Use Oklahoma Tribal Statistical Area'), (64091, u'Ranch'), (64092, u'State Designated American Indian Statistical Area'), (64093, u'Indian Village'), (64095, u'Indian Community'), (64096, u'American Indian Off-Reservation Trust Land')]
    ownerclass_domain = [(0, u'Unknown'), (1, u'Federal'), (2, u'Tribal'), (3, u'State'), (4, u'Regional'), (5, u'County'), (6, u'Municipal'), (7, u'Private')]
    objectid = models.IntegerField(null=True, blank=True, unique=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    fcode = models.IntegerField(choices=nativeamericanreservation_fcode, null=True, blank=True)
    nativeamericanarea_fipscode = models.CharField(max_length=5, null=True, blank=True)
    admintype = models.IntegerField(choices=ownerclass_domain, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    geom = models.PolygonField()

    @property
    def fips(self):
        return self.nativeamericanarea_fipscode


class CountyorEquivalent(USGSBase):
    service_id = 13
    countyorequivalent_fcode = [(61200, u'County'), (61201, u'Borough'), (61210, u'City and Borough'), (61202, u'District'), (61203, u'Independent City'), (61204, u'Island'), (61205, u'Judicial Division'), (61206, u'Municipality'), (61207, u'Municipio'), (61208, u'Parish'), (61299, u'Other County Equivalent Area')]
    objectid = models.IntegerField(null=True, blank=True, unique=True)
    fcode = models.IntegerField(choices=countyorequivalent_fcode, null=True, blank=True)
    state_fipscode = models.CharField(max_length=2, null=True, blank=True)
    state_name = models.CharField(max_length=120, null=True, blank=True)
    county_fipscode = models.CharField(max_length=3, null=True, blank=True)
    county_name = models.CharField(max_length=120, null=True, blank=True)
    stco_fipscode = models.CharField(max_length=5, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    geom = models.PolygonField()

    @property
    def fips(self):
        return self.stco_fipscode

    @property
    def name(self):
        return self.county_name

    class Meta:
        verbose_name = 'County (or Equivalent)'

    def __unicode__(self):
        return u'{name}, {state}'.format(name=self.county_name, state=self.state_name)



class IncorporatedPlace(USGSBase):
    service_id = 14
    incorporatedplace_fcode = [(61400, u'Incorporated Place'), (61401, u'Borough'), (61403, u'City'), (61404, u'City and Borough'), (61405, u'Communidad'), (61407, u'Consolidated City'), (61410, u'Independent City'), (61412, u'Municipality'), (61414, u'Town'), (61415, u'Village'), (61416, u'Zona Urbana')]
    yesno_domain = [(1, u'Yes'), (2, u'No'), (0, u'Unknown')]
    objectid = models.IntegerField(null=True, blank=True, unique=True)
    fcode = models.IntegerField(choices=incorporatedplace_fcode, null=True, blank=True)
    state_name = models.CharField(max_length=120, null=True, blank=True)
    place_fipscode = models.CharField(max_length=5, null=True, blank=True, verbose_name='FIPS Code')
    place_name = models.CharField(max_length=120, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    iscapitalcity = models.IntegerField(choices=yesno_domain, null=True, blank=True)
    iscountyseat = models.IntegerField(choices=yesno_domain, null=True, blank=True)
    geom = models.PolygonField()

    @property
    def fips(self):
        return self.place_fipscode

    @property
    def name(self):
        return self.place_name

    class Meta:
        ordering = ('state_name', 'place_name', )


class UnincorporatedPlace(USGSBase):
    service_id = 15
    unincorporatedplace_fcode_3 = [(61500, u'Unincorporated Place'), (61501, u'Census Designated Place'), (61502, u'Community / Town / Village'), (61503, u'Neighborhood'), (61504, u'Subdivision'), (61505, u'Communidad'), (61506, u'Zona Urbana')]
    objectid = models.IntegerField(null=True, blank=True, unique=True)
    fcode = models.IntegerField(choices=unincorporatedplace_fcode_3, null=True, blank=True)
    state_name = models.CharField(max_length=120, null=True, blank=True)
    place_fipscode = models.CharField(max_length=5, null=True, blank=True)
    place_name = models.CharField(max_length=120, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    geom = models.PolygonField()

    @property
    def fips(self):
        return self.place_fipscode

    @property
    def name(self):
        return self.place_name


class MinorCivilDivision(USGSBase):
    service_id = 16
    minorcivildivision_fcode = [(61300, u'Minor Civil Division'), (61302, u'Barrio'), (61304, u'Barrio - Pueblo'), (61306, u'Borough'), (61308, u'Census County Division'), (61310, u'Census Sub Area'), (61312, u'Census Sub District'), (61314, u'Charter Township'), (61316, u'City'), (61318, u'County'), (61320, u'District'), (61322, u'Gore'), (61324, u'Grant'), (61326, u'Incorporated Town'), (61328, u'Independent City'), (61330, u'Island'), (61332, u'Location'), (61334, u'Municipality'), (61336, u'Plantation'), (61338, u'Precinct'), (61340, u'Purchase'), (61342, u'Reservation'), (61344, u'Subbarrio'), (61346, u'Town'), (61348, u'Township'), (61350, u'Unorganized Territory'), (61352, u'Village')]
    objectid = models.IntegerField(null=True, blank=True, unique=True)
    fcode = models.IntegerField(choices=minorcivildivision_fcode, null=True, blank=True)
    state_name = models.CharField(max_length=120, null=True, blank=True)
    minorcivildivision_fipscode = models.CharField(max_length=10, null=True, blank=True)
    minorcivildivision_name = models.CharField(max_length=120, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    geom = models.PolygonField()

    @property
    def fips(self):
        return self.minorcivildivision_fipscode

    @property
    def name(self):
        return self.minorcivildivision_name


class StateorTerritoryHigh(USGSBase):
    service_id = 18
    stateorterritory_fcode = [(61100, u'State'), (61101, u'Territory'), (61102, u'Province')]
    objectid = models.IntegerField(null=True, blank=True, unique=True)
    fcode = models.IntegerField(choices=stateorterritory_fcode, null=True, blank=True)
    state_fipscode = models.CharField(max_length=2, null=True, blank=True)
    state_name = models.CharField(max_length=120, null=True, blank=True)
    population = models.IntegerField(null=True, blank=True)
    geom = models.PolygonField()

    @property
    def fips(self):
        return self.state_fipscode

    @property
    def name(self):
        return self.state_name

class CongressionalDistrict(USGSBase):
    service_id = 19
    firedistrict_fcode = [(62200, u'Fire District')]
    ownerclass_domain = [(0, u'Unknown'), (1, u'Federal'), (2, u'Tribal'), (3, u'State'), (4, u'Regional'), (5, u'County'), (6, u'Municipal'), (7, u'Private')]
    ownerormanagingagency_domain = [(1, u'Army Corps of Engineers'), (15, u'Bureau of Census'), (2, u'Bureau of Indian Affairs'), (3, u'Bureau of Land Management'), (4, u'Bureau of Reclamation'), (5, u'Department of Defense'), (6, u'Department of Energy'), (7, u'Department of Homeland Security'), (8, u'Department of Transportation'), (9, u'Department of Veteran Affairs'), (10, u'Fish and Wildlife Service'), (11, u'Forest Service'), (12, u'National Oceanic and Atmospheric Administration'), (13, u'National Park Service'), (14, u'Tennessee Valley Authority'), (99, u'Not Applicable')]
    objectid = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    fcode = models.IntegerField(choices=firedistrict_fcode, null=True, blank=True)
    designation = models.CharField(max_length=60, null=True, blank=True)
    state_fipscode = models.CharField(max_length=2, null=True, blank=True)
    state_name = models.CharField(max_length=120, null=True, blank=True)
    admintype = models.IntegerField(choices=ownerclass_domain, null=True, blank=True)
    ownerormanagingagency = models.IntegerField(choices=ownerormanagingagency_domain, null=True, blank=True)
    geom = models.PolygonField()

    @property
    def fips(self):
        return self.state_fipscode


################################
class GovUnits(models.Model):
    """
    Models the organizational units such as cities, counties, etc that have many fire stations.
    """

    STATES_CHOICES = [(state.abbr, state.name) for state in us.states.STATES]

    FCODE_CHOICES = [(61200, 'County'),
                     (61201, 'Borough'),
                     (61210, 'City and Borough'),
                     (61202, 'District'),
                     (61203, 'Independent City'),
                     (61204, 'Island'),
                     (61205, 'Judicial Division'),
                     (61206, 'Municipality'),
                     (61207, 'Municipio'),
                     (61208, 'Parish'),
                     (61299, 'Other County Equivalent Area')]

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
                                   ('A4', 'Emergency Service Provider - Free Distribution to Third Parties Via '
                                          'Internet'),
                                   ('B1', 'Government Agencies or Their Delegated Agents - Internal Use Only'),
                                   ('B2', 'Government Agencies or Their Delegated Agents - Bitmap Display Via Web'),
                                   ('B3', 'Government Agencies or Their Delegated Agents - Free Distribution to Third '
                                          'Parties'),
                                   ('B4', 'Government Agencies or Their Delegated Agents - Free Distribution to Third '
                                          'Parties Via Internet'),
                                   ('C1', 'Other Public or Educational Institutions - Internal Use Only'),
                                   ('C2', 'Other Public or Educational Institutions - Bitmap Display Via Web'),
                                   ('C3', 'Other Public or Educational Institutions - Free Distribution to Third '
                                          'Parties'),
                                   ('C4', 'Other Public or Educational Institutions - Free Distribution to Third '
                                          'Parties Via Internet'),
                                   ('D1', 'Data Contributors - Internal Use Only'), ('D2', 'Data Contributors - '
                                                                                           'Bitmap Display Via Web'),
                                   ('D3', 'Data Contributors - Free Distribution to Third Parties'),
                                   ('D4', 'Data Contributors - Free Distribution to Third Parties Via Internet'),
                                   ('E1', 'Public Domain - Internal Use Only'), ('E2', 'Public Domain - Bitmap '
                                                                                       'Display Via Web'),
                                   ('E3', 'Public Domain - Free Distribution to Third Parties'),
                                   ('E4', 'Public Domain - Free Distribution to Third Parties Via Internet')]

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objectid = models.IntegerField(unique=True, null=True, blank=True)
    permanent_identifier = models.CharField(max_length=40, null=True, blank=True)
    source_featureid = models.CharField(max_length=40, null=True, blank=True)
    source_datasetid = models.CharField(max_length=40, null=True, blank=True)
    source_datadesc = models.CharField(max_length=100, null=True, blank=True)
    source_originator = models.CharField(max_length=130, null=True, blank=True)
    data_security = models.IntegerField(blank=True, null=True, choices=DATA_SECURITY_CHOICES)
    distribution_policy = models.CharField(max_length=4, choices=DISTRIBUTION_POLICY_CHOICES, null=True, blank=True)
    loaddate = models.DateTimeField(null=True, blank=True)
    ftype = models.CharField(blank=True, null=True, max_length=50)
    fcode = models.IntegerField(blank=True, null=True, choices=FCODE_CHOICES)
    state_fipscode = models.CharField(max_length=2, null=True, blank=True)
    state_name = models.CharField(max_length=120, null=True, blank=True)
    county_fipscode = models.CharField(max_length=3, null=True, blank=True)
    county_name = models.CharField(max_length=120, null=True, blank=True)
    population = models.IntegerField(blank=True, null=True)
    gnis_id = models.CharField(max_length=10, null=True, blank=True)
    fips = models.CharField(max_length=10, blank=True, null=True)
    globalid = models.CharField(max_length=38, null=True, blank=True)
    geom = models.PolygonField()

    objects = models.GeoManager()

    @property
    def origin_uri(self):
        """
        This object's URI (from the national map).
        """
        return 'http://services.nationalmap.gov/arcgis/rest/services/govunits/MapServer/10/{0}?f=json' \
            .format(self.objectid)

    @classmethod
    def load_data(cls):
        # Still need to load from jurisdictions
        from django.contrib.gis.geos import LinearRing, Polygon
        for endpoint in [11, 12, 14, 15, 16, 17, 18, 19]:
            objects = requests.get('http://services.nationalmap.gov/arcgis/rest/services/govunits/MapServer/{0}/query?'
                                   'where=1%3D1&text=&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&'
                                   'spatialRel=esriSpatialRelIntersects&relationParam=&outFields=&returnGeometry=true&'
                                   'maxAllowableOffset=&geometryPrecision=&outSR=&returnIdsOnly=true&returnCountOnly=false&'
                                   'orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&'
                                   'gdbVersion=&returnDistinctValues=false&f=json'.format(endpoint))

            current_ids = set(cls.objects.all().values_list('objectid', flat=True))
            object_ids = set(json.loads(objects.content)['objectIds']) - current_ids
            url = 'http://services.nationalmap.gov/arcgis/rest/services/govunits/MapServer/{1}/{0}?f=json'

            for object in object_ids:
                try:

                    if cls.objects.filter(objectid=object):
                        continue

                    obj = requests.get(url.format(object, endpoint))
                    obj = json.loads(obj.content)
                    #import ipdb; ipdb.set_trace()
                    data = dict((k.lower(), v) for k, v in obj['feature']['attributes'].iteritems())

                    for key in data.keys():
                        if key not in [field.name for field in cls._meta.fields]:
                            data.pop(key)

                    if obj['feature'].get('geometry'):
                        poly = map(LinearRing, obj['feature']['geometry']['rings'])
                        data['geom'] = Polygon(*poly)

                    data['loaddate'] = datetime.datetime.fromtimestamp(data['loaddate']/1000.0)
                    feat = cls.objects.create(**data)
                    feat.save()
                    print 'Saved object: {0}'.format(data.get('name'))
                    print '{0} Counties loaded.'.format(cls.objects.all().count())

                except KeyError:
                    print '{0} failed.'.format(object)
                    print url.format(object, endpoint)

                except IntegrityError:
                    print '{0} failed.'.format(object)
                    print url.format(object, endpoint)
                    print sys.exc_info()

                    try:
                        rollback()
                    except:
                        pass

                except:
                    print '{0} failed.'.format(object)
                    print url.format(object, endpoint)
                    print sys.exc_info()

    class Meta:
        ordering = ('state_name', 'county_name')
        verbose_name_plural = 'Government Units'
        verbose_name = 'Government Unit'

    def __unicode__(self):
        return u'{name}, {state}'.format(name=self.county_name, state=self.state_name)