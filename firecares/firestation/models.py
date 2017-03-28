import datetime
import json
import requests
import sys
import csv
import os
import re
from .managers import PriorityDepartmentsManager, CalculationManager
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point, MultiPolygon
from django.contrib.gis.measure import D
from django.core.validators import MaxValueValidator
from django.db import connections
from django.utils.text import slugify
from firecares.firecares_core.models import RecentlyUpdatedMixin, Archivable
from django.core.urlresolvers import reverse
from django.db.transaction import rollback
from django.db.utils import IntegrityError
from django.utils.functional import cached_property
from django.utils.deconstruct import deconstructible
from firecares.firecares_core.models import Address
from firecares.firecares_core.validators import validate_choice
from firecares.utils import IntChoiceEnum
from numpy import histogram
from phonenumber_field.modelfields import PhoneNumberField
from firecares.firecares_core.models import Country
from genericm2m.models import RelatedObjectsDescriptor
from reversion import revisions as reversion
from storages.backends.s3boto import S3BotoStorage
from .metrics import FireDepartmentMetrics
from guardian.shortcuts import assign_perm, remove_perm, get_users_with_perms
from annoying.fields import JSONField


class HazardLevels(IntChoiceEnum):
    All = 0
    Low = 1
    Medium = 2
    High = 4
    Unknown = 5

    @classmethod
    def coerce(cls, name):
        if name.lower() == 'n/a' or name.lower() == 'na':
            return cls.Unknown
        elif name.lower() == 'low':
            return cls.Low
        elif name.lower() == 'medium' or name.lower() == 'med':
            return cls.Medium
        elif name.lower() == 'high':
            return cls.High
        elif name.lower() == 'all':
            return cls.All
        else:
            raise KeyError

    @classmethod
    def values(cls):
        return sorted(map(int, cls))

    @classmethod
    def values_sans_all(cls):
        return sorted(filter(lambda x: x != cls.All.value, cls.values()))


class USGSStructureData(models.Model):
    """
    Models structure data from the USGS National Map.

    Schema from: http://services.nationalmap.gov/arcgis/rest/services/structures/MapServer/1?f=json
    """
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

    FCODE_CHOICES = [(81000, 'Transportation Facility'),
                     (81006, 'Airport Terminal'),
                     (81008, 'Air Support / Maintenance Facility'),
                     (81010, 'Air Traffic Control Center / Command Center'),
                     (81011, 'Boat Ramp / Dock'),
                     (81012, 'Bridge'),
                     (81014, 'Bridge:  Light Rail / Subway'),
                     (81016, 'Bridge:  Railroad'),
                     (81018, 'Bridge:  Road'),
                     (81020, 'Border Crossing / Port of Entry'),
                     (81022, 'Bus Station / Dispatch Facility'),
                     (81024, 'Ferry Terminal / Dispatch Facility'),
                     (81025, 'Harbor / Marina'),
                     (81026, 'Helipad / Heliport / Helispot'),
                     (81028, 'Launch Facility'),
                     (81030, 'Launch Pad'),
                     (81032, 'Light Rail Power Substation'),
                     (81034, 'Light Rail Station'),
                     (81036, 'Park and Ride / Commuter Lot'),
                     (81038, 'Parking Lot Structure / Garage'),
                     (81040, 'Pier / Wharf / Quay / Mole'),
                     (81042, 'Port Facility'),
                     (81044, 'Port Facility: Commercial Port'),
                     (81046, 'Port Facility: Crane'),
                     (81048, 'Port Facility: Maintenance and Fuel Facility'),
                     (81050, 'Port Facility: Modal Transfer Facility'),
                     (81052, 'Port Facility: Passenger Terminal'),
                     (81054, 'Port Facility: Warehouse Storage / Container Yard'),
                     (81056, 'Railroad Facility'),
                     (81058, 'Railroad Command / Control Facility'),
                     (81060, 'Railroad Freight Loading Facility'),
                     (81062, 'Railroad Maintenance / Fuel Facility'),
                     (81064, 'Railroad Roundhouse / Turntable'),
                     (81066, 'Railroad Station'),
                     (81068, 'Railroad Yard'),
                     (81070, 'Rest Stop / Roadside Park'),
                     (81072, 'Seaplane Anchorage / Base'),
                     (81073, 'Snowshed'),
                     (81074, 'Subway Station'),
                     (81076, 'Toll Booth / Plaza'),
                     (81078, 'Truck Stop'),
                     (81080, 'Tunnel'),
                     (81082, 'Tunnel:  Light Rail / Subway'),
                     (81084, 'Tunnel:  Road'),
                     (81086, 'Tunnel:  Railroad'),
                     (81088, 'Weigh Station / Inspection Station')]

    ISLANDMARK_CHOICES = [(1, 'Yes'),
                          (2, 'No'),
                          (0, 'Unknown')]

    POINTLOCATIONTYPE_CHOICES = [(0, 'Unknown'),
                                 (1, 'Centroid'),
                                 (2, 'Egress or Entrance'),
                                 (3, 'Turn-off location'),
                                 (4, 'Approximate')]

    ADMINTYPE_CHOICES = [(0, 'Unknown'),
                         (1, 'Federal'),
                         (2, 'Tribal'),
                         (3, 'State'),
                         (4, 'Regional'),
                         (5, 'County'),
                         (6, 'Municipal'),
                         (7, 'Private')]

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
    name = models.CharField(max_length=100, null=True, blank=True)
    islandmark = models.IntegerField(null=True, blank=True, choices=ISLANDMARK_CHOICES, verbose_name='Landmark')
    pointlocationtype = models.IntegerField(null=True, blank=True, choices=POINTLOCATIONTYPE_CHOICES,
                                            verbose_name='Point Type')
    admintype = models.IntegerField(null=True, blank=True, choices=ADMINTYPE_CHOICES)
    addressbuildingname = models.CharField(max_length=60, null=True, blank=True, verbose_name='Building Name')
    address = models.CharField(max_length=75, null=True, blank=True)
    city = models.CharField(max_length=40, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    zipcode = models.CharField(max_length=10, null=True, blank=True)
    gnis_id = models.CharField(max_length=10, null=True, blank=True)
    foot_id = models.CharField(max_length=40, null=True, blank=True)
    complex_id = models.CharField(max_length=40, null=True, blank=True)
    globalid = models.CharField(max_length=38, null=True, blank=True)
    geom = models.PointField()
    objects = models.GeoManager()

    def __unicode__(self):
        return u'{state}, {city}, {name}'.format(name=self.name, state=self.state, city=self.city)

    def full_address(self):
        return u'{address}, {city}, {state}, {zipcode}'.format(address=self.address, city=self.city, state=self.state,
                                                               zipcode=self.zipcode)

    class Meta:
        ordering = ('state', 'city', 'name')

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


class IntersectingDepartmentLog(models.Model):
    """
    Keeps track of departments removed from other departments.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('FireDepartment', related_name='intersecting_department')
    removed_department = models.ForeignKey('FireDepartment', related_name='removed_intersecting_departments')

    def __unicode__(self):
        return u'Removed {} from {}.'.format(self.removed_department.name, self.parent.name)


class FireDepartment(RecentlyUpdatedMixin, Archivable, models.Model):
    """
    Models Fire Departments.
    """

    DEPARTMENT_TYPE_CHOICES = [
        ('Volunteer', 'Volunteer'),
        ('Mostly Volunteer', 'Mostly Volunteer'),
        ('Career', 'Career'),
        ('Mostly Career', 'Mostly Career'),
    ]

    REGION_CHOICES = [
        ('Northeast', 'Northeast'),
        ('West', 'West'),
        ('South', 'South'),
        ('Midwest', 'Midwest'),
        (None, '')
    ]

    POPULATION_CLASSES = [
        (0, 'Population less than 2,500.'),
        (1, 'Population between 2,500 and 4,999.'),
        (2, 'Population between 5,000 and 9,999.'),
        (3, 'Population between 10,000 and 24,999.'),
        (4, 'Population between 25,000 and 49,999.'),
        (5, 'Population between 50,000 and 99,999.'),
        (6, 'Population between 100,000 and 249,999.'),
        (7, 'Population between 250,000 and 499,999.'),
        (8, 'Population between 500,000 and 999,999.'),
        (9, 'Population greater than 1,000,000.'),
    ]

    def __init__(self, *args, **kwargs):
        self.metrics = FireDepartmentMetrics(self, PopulationClassQuartile, NationalCalculations)
        super(FireDepartment, self).__init__(*args, **kwargs)

    created = models.DateTimeField(auto_now=True)
    modified = models.DateTimeField(auto_now=True)
    fdid = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    headquarters_address = models.ForeignKey(Address, null=True, blank=True, related_name='firedepartment_headquarters')
    mail_address = models.ForeignKey(Address, null=True, blank=True)
    domain_name = models.CharField(max_length=255, blank=True, null=True)
    headquarters_phone = PhoneNumberField(null=True, blank=True)
    headquarters_fax = PhoneNumberField(null=True, blank=True)
    department_type = models.CharField(max_length=20, choices=DEPARTMENT_TYPE_CHOICES, null=True, blank=True)
    organization_type = models.CharField(max_length=75, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    state = models.CharField(max_length=2, db_index=True)
    region = models.CharField(max_length=20, db_index=True, choices=REGION_CHOICES, null=True, blank=True)
    geom = models.MultiPolygonField(null=True, blank=True)
    objects = CalculationManager()
    priority_departments = PriorityDepartmentsManager()
    government_unit = RelatedObjectsDescriptor()
    population = models.IntegerField(null=True, blank=True)
    population_class = models.IntegerField(null=True, blank=True, choices=POPULATION_CLASSES, db_index=True)
    featured = models.BooleanField(default=False, db_index=True)
    iaff = models.CharField(max_length=25, blank=True, null=True)
    twitter_handle = models.CharField(max_length=255, blank=True, null=True)
    owned_tracts_geom = models.MultiPolygonField(null=True, blank=True)

    class Meta:
        ordering = ('name',)
        index_together = [
            ['population', 'id', 'region'],
            ['population', 'region']
        ]
        # Department curation will be done via the built-in "change_firedepartment" permission
        permissions = (
            ('admin_firedepartment', 'Can administer department users'),
        )

    def reload_metrics(self):
        self.metrics = FireDepartmentMetrics(self, PopulationClassQuartile, NationalCalculations)

    @property
    def headquarters_geom(self):
        return getattr(self.headquarters_address, 'geom', None)

    @property
    def government_unit_objects(self):
        """
        Memoize the government_unit generic key lookup.
        """
        if not getattr(self, '_government_unit_objects', None):
            self._government_unit_objects = self.government_unit.all().generic_objects()

        return self._government_unit_objects

    @property
    def fips(self):
        objs = self.government_unit_objects

        if objs:
            return [obj.fips for obj in objs if hasattr(obj, 'fips')]

        return []

    @property
    def geom_area(self):
        """
        Project the department's geometry into US National Atlas Equal Area
        Returns mi2
        """
        if self.geom:
            try:
                return (self.geom.transform(2163, clone=True).area / 1000000) * 0.386102
            except:
                return

    def get_population_class(self):
        """
        Returns the population class of a department based on NFPA community sizes categories as an integer.

        9: > 1,000,000
        8: (500000, 999999)
        7: (250000, 499999)
        6: (100000, 249999)
        5: (50000, 99999)
        4: (25000, 49999)
        3: (10000, 24999)
        2: (5000, 9999)
        1: (2500, 4999)
        0: < 2500
        """
        if self.population is None:
            return

        if self.population < 2500:
            return 0

        if self.population >= 1000000:
            return 9

        community_sizes = [
            (500000, 999999),
            (250000, 499999),
            (100000, 249999),
            (50000, 99999),
            (25000, 49999),
            (10000, 24999),
            (5000, 9999),
            (2500, 4999)]

        for clazz, min_max in zip(reversed(range(1, 9)), community_sizes):
            if min_max[0] <= self.population <= min_max[1]:
                return clazz

    @property
    def similar_departments(self, ignore_regions_min=1000000):
        """
        Identifies similar departments based on the protected population size and region.
        """

        params = {'archived': self.archived}

        if self.population >= 1000000:
            params['population__gte'] = 1000000

        elif self.population < 2500:
            params['population__lt'] = 2500

        else:
            community_sizes = [
                (500000, 999999),
                (250000, 499999),
                (100000, 249999),
                (50000, 99999),
                (25000, 49999),
                (10000, 24999),
                (5000, 9999),
                (2500, 4999)]

            for lower_bound, upper_bound in community_sizes:
                if lower_bound <= self.population <= upper_bound:
                    params['population__lte'] = upper_bound
                    params['population__gte'] = lower_bound

        similar = FireDepartment.objects.filter(**params)\
            .exclude(id=self.id)\
            .extra(select={'difference': "abs(population - %s)"}, select_params=[self.population])\
            .extra(order_by=['difference'])

        # Large departments may not have similar departments in their region.
        if self.population < ignore_regions_min:
            similar = similar.filter(region=self.region)

        return similar

    @property
    def thumbnail_name(self):
        return slugify(' '.join(['us', self.state, self.name])) + '.jpg'

    @property
    def thumbnail_name_no_marker(self):
        return slugify(' '.join(['us', self.state, self.name, 'no marker'])) + '.jpg'

    @property
    def thumbnail(self):
        return 'https://static.firecares.org/department-thumbnails/{0}'.format(self.thumbnail_name)

    @property
    def thumbnail_no_marker(self):
        return 'https://static.firecares.org/department-thumbnails/{0}' \
            .format(self.thumbnail_name_no_marker)

    def generate_thumbnail(self, marker=True):
        geom = None

        if self.geom:
            geom = self.geom.centroid
        elif self.headquarters_address and self.headquarters_address.geom:
            geom = self.headquarters_address.geom
        else:
            return '/static/firestation/theme/assets/images/content/property-1.jpg'

        if marker and geom:
            marker = 'pin-l-embassy+0074D9({geom.x},{geom.y})/'.format(geom=geom)

        return 'http://api.tiles.mapbox.com/v4/garnertb.mmlochkh/{marker}' \
               '{geom.x},{geom.y},8/500x300.jpg?access_token={access_token}'.format(marker=marker,
                                                                                    geom=geom,
                                                                                    access_token=getattr(settings, 'MAPBOX_ACCESS_TOKEN', ''))

    def set_geometry_from_government_unit(self):
        def _first(arr):
            if arr and len(arr):
                return arr[0]
            else:
                return None

        geom_containers = self.government_unit_objects + [self]
        objs = [x.geom.buffer(0) for x in geom_containers if getattr(x, 'geom', None)]

        if objs:
            geom = objs.pop()
            for g in objs:
                geom = geom.union(g)
            self.geom = MultiPolygon(geom) if geom.geom_type == 'Polygon' else geom
            self.save()

    def set_population_from_government_unit(self):
        """
        Stores the population of government units on the FD object to speed up querying.
        """
        objs = self.government_unit_objects

        if objs:

            for gov_unit in objs:
                pop = getattr(gov_unit, 'population', None)

                if pop is not None:
                    if self.population is None:
                        self.population = 0

                    self.population += pop
        else:
            self.population = None

        self.population_class = self.get_population_class()
        self.save()

    @classmethod
    def get_histogram(cls, field, bins=400):
        hist = histogram(list(cls.objects.filter(**{'{0}__isnull'.format(field): False})
                         .values_list(field, flat=True)), bins=bins)
        return json.dumps(zip(hist[1], hist[0]), separators=(',', ':'))

    def set_region(self, region):
        validate_choice(FireDepartment.REGION_CHOICES)(region)
        self.region = region
        self.save()

    @cached_property
    def description(self):
        """
        A text description of the department used for displaying on the client side.
        """
        try:
            name = self.name

            if not self.name.lower().endswith('department') and not self.name.lower().endswith('district'):
                name += ' fire department'

            return "The {name} is a {department_type} department located in the {object.region} NFPA region and headquartered in " \
                   "{object.headquarters_address.city}, {object.headquarters_address.state_province}."\
                .format(name=name,
                        department_type=self.department_type.lower(),
                        object=self).strip()
        except:
            return 'No description for Fire Department'

    @classmethod
    def load_from_usfa_csv(cls):
        """
        Loads Fire Departments from http://apps.usfa.fema.gov/census-download.
        """
        us, _ = Country.objects.get_or_create(name='United States of America', iso_code='US')

        with open(os.path.join(os.path.dirname(__file__), 'scripts/usfa-census-national.csv'), 'r') as csvfile:

            # This only runs once, since there isn't a good key to identify duplicates
            if not cls.objects.all().count():
                reader = csv.DictReader(csvfile)
                counter = 0
                for row in reader:
                    # only run once.
                    hq_address_params = {}
                    hq_address_params['address_line1'] = row.get('HQ Addr1')
                    hq_address_params['address_line2'] = row.get('HQ Addr2')
                    hq_address_params['city'] = row.get('HQ City')
                    hq_address_params['state_province'] = row.get('HQ State')
                    hq_address_params['postal_code'] = row.get('HQ Zip')
                    hq_address_params['country'] = us
                    headquarters_address, _ = Address.objects.get_or_create(**hq_address_params)
                    headquarters_address.save()

                    mail_address_params = {}
                    mail_address_params['address_line1'] = row.get('Mail Addr1')
                    mail_address_params['address_line2'] = row.get('Mail Addr2') or row.get('Mail PO Box')
                    mail_address_params['city'] = row.get('Mail City')
                    mail_address_params['state_province'] = row.get('Mail State')
                    mail_address_params['postal_code'] = row.get('Mail Zip')
                    mail_address_params['country'] = us
                    mail_address, _ = Address.objects.get_or_create(**mail_address_params)
                    mail_address.save()

                    params = {}
                    params['fdid'] = row.get('FDID')
                    params['name'] = row.get('Fire Dept Name')
                    params['headquarters_phone'] = row.get('HQ Phone')
                    params['headquarters_fax'] = row.get('HQ Fax')
                    params['department_type'] = row.get('Dept Type')
                    params['organization_type'] = row.get('Organization Type')
                    params['website'] = row.get('Website')
                    params['headquarters_address'] = headquarters_address
                    params['mail_address'] = mail_address
                    params['state'] = row.get('HQ State')

                    cls.objects.create(**params)
                    counter += 1

                assert counter == cls.objects.all().count()

    @cached_property
    def slug(self):
        return slugify(self.name)

    def get_absolute_url(self):
        return reverse('firedepartment_detail_slug', kwargs=dict(pk=self.id, slug=self.slug))

    def find_jurisdiction(self):
        from firecares.usgs.models import CountyorEquivalent, IncorporatedPlace, UnincorporatedPlace

        counties = CountyorEquivalent.objects.filter(state_name='Virginia')
        for county in counties:
            incorporated = IncorporatedPlace.objects.filter(geom__intersects=county.geom)
            unincoporated = UnincorporatedPlace.objects.filter(geom__intersects=county.geom)
            station = FireStation.objects.filter(geom__intersects=county.geom)

            print 'County', county.name
            print 'Incorporated Place', incorporated.count()
            print 'Unincorporated Place', unincoporated.count()
            print 'Stations:', station

    def __unicode__(self):
        return self.name

    def remove_from_department(self, department):
        """
        Removes a departments geometry and population from this department's.
        """
        if self.geom and department.geom:
            try:
                self.geom = MultiPolygon(self.geom.difference(department.geom))
            except TypeError:
                self.geom = self.geom.difference(department.geom)

        if department.population and self.population:
            self.population = self.population - department.population
            self.population_class = self.get_population_class()

        IntersectingDepartmentLog.objects.create(parent=self, removed_department=department)
        self.save()

    def get_department_admins(self):
        return filter(lambda x: x.has_perm('admin_firedepartment', self), get_users_with_perms(self))

    def get_department_curators(self):
        return filter(lambda x: x.has_perm('change_firedepartment', self), get_users_with_perms(self))

    def add_admin(self, user):
        assign_perm('admin_firedepartment', user, self)

    def remove_admin(self, user):
        remove_perm('admin_firedepartment', user, self)

    def is_admin(self, user):
        return user.has_perm('admin_firedepartment', self)

    def add_curator(self, user):
        assign_perm('change_firedepartment', user, self)

    def remove_curator(self, user):
        remove_perm('change_firedepartment', user, self)

    def is_curator(self, user):
        return user.has_perm('change_firedepartment', self)

    def get_users_with_permissions(self):
        return get_users_with_perms(self)


class FireDepartmentRiskModels(models.Model):
    class Meta:
        unique_together = ['level', 'department']

    level = models.IntegerField(choices=HazardLevels.choices(), default=1)
    department = models.ForeignKey(FireDepartment)
    dist_model_score = models.FloatField(null=True, blank=True, editable=False, db_index=True)

    risk_model_deaths = models.FloatField(null=True, blank=True, db_index=True,
                                          verbose_name='Predicted deaths per year.')

    risk_model_injuries = models.FloatField(null=True, blank=True, db_index=True,
                                            verbose_name='Predicted injuries per year.')

    risk_model_fires = models.FloatField(null=True, blank=True, db_index=True,
                                         verbose_name='Predicted number of fires per year.')

    risk_model_fires_size0 = models.FloatField(null=True, blank=True, db_index=True,
                                               verbose_name='Predicted number of size 0 fires.')

    risk_model_fires_size0_percentage = models.FloatField(null=True, blank=True,
                                                          verbose_name='Percentage of size 0 fires.')

    risk_model_fires_size1 = models.FloatField(null=True, blank=True, db_index=True,
                                               verbose_name='Predicted number of size 1 fires.')

    risk_model_fires_size1_percentage = models.FloatField(null=True, blank=True,
                                                          verbose_name='Percentage of size 1 fires.')

    risk_model_fires_size2 = models.FloatField(null=True, blank=True, db_index=True,
                                               verbose_name='Predicted number of size 2 firese.')

    risk_model_fires_size2_percentage = models.FloatField(null=True, blank=True,
                                                          verbose_name='Percentage of size 2 fires.')

    structure_count = models.IntegerField(null=True, blank=True,
                                          verbose_name='Structure counts for this hazard level over department\'s owned census tracts')

    floor_count_coefficients = JSONField(null=True, blank=True)

    dist_model_score_fire_count = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return '{level} risk - {department} ({f_id})'.format(level=HazardLevels(self.level).name, department=self.department, f_id=self.department.id)


class FireStation(USGSStructureData, Archivable):
    """
    Fire Stations.
    """
    service_id = 7

    fdid = models.CharField(max_length=10, null=True, blank=True)
    department = models.ForeignKey(FireDepartment, null=True, blank=True, on_delete=models.SET_NULL)
    station_number = models.IntegerField(null=True, blank=True)
    station_address = models.ForeignKey(Address, null=True, blank=True)
    district = models.MultiPolygonField(null=True, blank=True)
    objects = models.GeoManager()

    @classmethod
    def create_station(cls, address_string, department, **kwargs):
        """
        Convenience method used to create new stations.
        """
        addy = Address.create_from_string(address_string)

        station = FireStation(department=department,
                              station_address=addy,
                              address=addy.address_line1,
                              state=addy.state_province,
                              city=addy.city,
                              zipcode=addy.postal_code,
                              geom=addy.geom,
                              **kwargs)

        if not kwargs.get('station_number'):
            station.station_number = station.station_number_from_name()

            if station.station_number:
                station.station_number = int(station.station_number)

        station.save()
        return station

    def station_number_from_name(self):
        """
        Pulls the station number out of the name.
        """

        match = re.search(r'((?<=Station\s)|(?<=Engine\s))\b\d+', self.name)

        if match:
            return match.group()

        match = re.search(r'(?<!Battalion\s)\b\d+', self.name)

        if match:
            return match.group()

    @classmethod
    def populate_address(cls):
        us, _ = Country.objects.get_or_create(iso_code='US')
        for obj in cls.objects.filter(station_address__isnull=True, address__isnull=False, zipcode__isnull=False):
            try:
                addr, _ = Address.objects.get_or_create(address_line1=obj.address, city=obj.city,
                                                        state_province=obj.state, postal_code=obj.zipcode,
                                                        country=us, defaults=dict(geom=obj.geom))
            except Address.MultipleObjectsReturned:
                pass
            obj.station_address = addr
            obj.save()

    @property
    def origin_uri(self):
        """
        This object's URI (from the national map).
        """
        return 'http://services.nationalmap.gov/arcgis/rest/services/structures/MapServer/7/{0}?f=json' \
            .format(self.objectid)

    @classmethod
    def load_data(cls):
        objects = requests.get('http://services.nationalmap.gov/arcgis/rest/services/structures/MapServer/7/query?'
                               'where=1%3D1&text=&objectIds=&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&'
                               'spatialRel=esriSpatialRelIntersects&relationParam=&outFields=&returnGeometry=true&'
                               'maxAllowableOffset=&geometryPrecision=&outSR=&returnIdsOnly=true&returnCountOnly=false&'
                               'orderByFields=&groupByFieldsForStatistics=&outStatistics=&returnZ=false&returnM=false&'
                               'gdbVersion=&returnDistinctValues=false&f=json')

        current_ids = set(FireStation.objects.all().values_list('objectid', flat=True))
        object_ids = set(json.loads(objects.content)['objectIds']) - current_ids
        url = 'http://services.nationalmap.gov/arcgis/rest/services/structures/MapServer/7/{0}?f=json'
        us, _ = Country.objects.get_or_create(iso_code='US')

        for object in object_ids:
            try:

                if FireStation.objects.filter(objectid=object):
                    continue

                obj = requests.get(url.format(object))
                obj = json.loads(obj.content)
                data = dict((k.lower(), v) for k, v in obj['feature']['attributes'].iteritems())

                if obj['feature'].get('geometry'):
                    data['geom'] = Point(obj['feature']['geometry']['x'], obj['feature']['geometry']['y'])

                data['loaddate'] = datetime.datetime.fromtimestamp(data['loaddate'] / 1000.0)
                feat = cls.objects.create(**data)
                feat.save()
                print 'Saved object: {0}'.format(data.get('name'))
                print '{0} Firestations loaded.'.format(FireStation.objects.all().count())

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
    def district_area(self):
        """
        Project the district's geometry into US National Atlas Equal Area
        Returns mi2
        """
        if self.district:
            try:
                return (self.district.transform(102009, clone=True).area / 1000000) * 0.38610
            except:
                return

    def suggested_departments(self):
        """
        Helper functions
        """
        def filter_words_from_name(name, words_to_filter):
            removed_dict = dict((re.escape(k), v) for k, v in words_to_filter.iteritems())
            removed_pattern = re.compile("|".join(removed_dict.keys()))
            name = removed_pattern.sub(lambda m: removed_dict[re.escape(m.group(0))], name)
            name = re.sub("^\d+\s|\s\d+\s|\s\d+$", " ", name)
            name = re.sub(' +', ' ', name)
            name = name.strip()
            return name

        def determine_insertion_index(suggested_departments, department_count, score):
            index = 1
            while index < department_count:
                if score > suggested_departments[index].department_score:
                    break
                index += 1
            return index

        always_removed_words = {
            "Station": "",
            " Engine": "",
            " Truck": "",
            " Ladder": "",
            " Quint": "",
            " Squirt": "",
            " Ambulance": "",
            " Service": "",
            " District": "",
            " Headquarters": "",
            " City": ""}
        lev_removed_words = {
            " Rescue": "",
            " Service": "",
            " and": "",
            " Emergency": "",
            " Medical": "",
            " Services": ""}

        filtered_name = self.name
        filtered_name = filter_words_from_name(filtered_name, always_removed_words)
        lev_filtered_name = filter_words_from_name(filtered_name, lev_removed_words)

        nearby_departments = FireDepartment.objects.filter(headquarters_address__geom__distance_lte=(self.geom, D(mi=40)))\
            .distance(self.geom)\
            .extra(select={'dis_name': "select levenshtein(firestation_firedepartment.name, %s)", 'dis_sound': "select similarity(firestation_firedepartment.name, %s)"},
                   select_params=(lev_filtered_name, filtered_name,))\
            .order_by('distance', 'dis_name')

        best_department_score = 0
        max_suggested_departments = 10
        suggested_departments = list()

        for n, fireDepartment in enumerate(nearby_departments):

            if n == 100:
                break

            department_distance = 40

            if fireDepartment.distance is not None:
                department_distance = fireDepartment.distance.mi
            else:
                meterStation = self.geom.transform(3857, True)
                meterDepartment = self.geom.transform(3857, True)
                department_distance = meterDepartment.distance(meterStation) * 0.000621371

            #  The maximum return from levenshtein will be the length of the longer string
            #  so to create a true 0-1 ratio find the longer string name

            station_name_length = len(lev_filtered_name)
            department_name_length = len(fireDepartment.name)
            minimum_name_length = min(station_name_length, department_name_length)
            longest_name_length = max(station_name_length, department_name_length)
            minimum_lev_distance = longest_name_length - minimum_name_length

            #  lower bound of levenshtein is at least difference of strings
            #  to create zero to one ratio must subtract minimum distances

            fireDepartment.dis_name = max(fireDepartment.dis_name - minimum_lev_distance, 0)

            department_score = ((1 - department_distance / 40) * 55) + (1 - fireDepartment.dis_name / longest_name_length) * 80 + (fireDepartment.dis_sound * 30)

            fireDepartment.distance = department_distance
            fireDepartment.department_score = department_score

            if department_score > best_department_score:
                best_department_score = department_score
                suggested_departments.insert(0, fireDepartment)
            else:
                num_departments = len(suggested_departments)
                if num_departments < max_suggested_departments or (num_departments >= max_suggested_departments and department_score > suggested_departments[max_suggested_departments - 1].department_score):
                    department_index = determine_insertion_index(suggested_departments, num_departments, department_score)
                    suggested_departments.insert(department_index, fireDepartment)

        #  Trim list down to max count

        num_departments = len(suggested_departments)
        while num_departments > max_suggested_departments:
            suggested_departments.pop()
            num_departments -= 1

        return suggested_departments

    @cached_property
    def slug(self):
        return slugify(self.name)

    def get_absolute_url(self):
        return reverse('firestation_detail_slug', kwargs=dict(pk=self.id, slug=self.slug))

    class Meta:
        verbose_name = 'Fire Station'


class Staffing(models.Model):
    """
    Models response capabilities (apparatus and responders).
    """
    APPARATUS_CHOICES = [('Engine', 'Engine'),
                         ('Ladder/Truck/Aerial', 'Ladder/Truck/Aerial'),
                         ('Quint', 'Quint'),
                         ('Ambulance/ALS', 'Ambulance/ALS'),
                         ('Ambulance/BLS', 'Ambulance/BLS'),
                         ('Heavy Rescue', 'Heavy Rescue'),
                         ('Boat', 'Boat'),
                         ('Hazmat', 'Hazmat'),
                         ('Chief', 'Chief'),
                         ('Other', 'Other')]

    # human friendly apparatus choices with <= 10 characters
    APPARATUS_SHAPEFILE_CHOICES = [('Engine', 'engine'),
                                   ('Ladder/Truck/Aerial', 'truck'),
                                   ('Quint', 'quint'),
                                   ('Ambulance/ALS', 'als_am'),
                                   ('Ambulance/BLS', 'bls_am'),
                                   ('Heavy Rescue', 'rescue'),
                                   ('Boat', 'boat'),
                                   ('Hazmat', 'hazmat'),
                                   ('Chief', 'chief'),
                                   ('Other', 'other')]

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    firestation = models.ForeignKey(FireStation)
    apparatus = models.CharField(choices=APPARATUS_CHOICES, max_length=20, default='Engine')
    personnel = models.PositiveIntegerField(null=True, blank=True, default=0, validators=[MaxValueValidator(99)])
    als = models.BooleanField(default=False)

    def __unicode__(self):
        return '{0} response capability for {1}'.format(self.apparatus, self.firestation)

    class Meta:
        verbose_name_plural = 'Response Capabilities'


class NFIRSStatistic(models.Model):
    """
    Caches NFIRS stats.
    """

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    fire_department = models.ForeignKey(FireDepartment)
    metric = models.CharField(max_length=50, db_index=True)
    year = models.PositiveSmallIntegerField(db_index=True)
    count = models.PositiveSmallIntegerField(db_index=True, null=True)
    level = models.IntegerField(choices=HazardLevels.choices(), default=1, db_index=True)

    class Meta:
        unique_together = ['fire_department', 'year', 'metric', 'level']
        ordering = ['-year', ]


class PopulationClassQuartile(models.Model):
    """
    Population Quartile Views
    """

    id = models.OneToOneField(FireDepartment, db_column='id', primary_key=True)
    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField(editable=False)
    fdid = models.CharField(max_length=10, editable=False)
    name = models.CharField(max_length=100, editable=False)
    headquarters_address = models.ForeignKey(Address, null=True, blank=True, editable=False, related_name='+')
    mail_address = models.ForeignKey(Address, null=True, blank=True, editable=False, related_name='+')
    headquarters_phone = PhoneNumberField(null=True, blank=True, editable=False)
    headquarters_fax = PhoneNumberField(null=True, blank=True, editable=False)
    department_type = models.CharField(max_length=20, null=True, blank=True, editable=False)
    organization_type = models.CharField(max_length=75, null=True, blank=True, editable=False)
    website = models.URLField(null=True, blank=True, editable=False)
    state = models.CharField(max_length=2, editable=False)
    region = models.CharField(max_length=20, null=True, blank=True, editable=False)
    geom = models.MultiPolygonField(null=True, blank=True, editable=False)
    objects = CalculationManager()
    level = models.IntegerField(choices=HazardLevels.choices(), default=1)
    dist_model_score = models.FloatField(null=True, blank=True, editable=False)

    risk_model_deaths = models.FloatField(null=True, blank=True, editable=False,
                                          verbose_name='Predicted deaths per year.')

    risk_model_injuries = models.FloatField(null=True, blank=True, editable=False,
                                            verbose_name='Predicted injuries per year.')

    risk_model_fires = models.FloatField(null=True, blank=True, editable=False,
                                         verbose_name='Predicted number of fires per year.')

    risk_model_fires_size0 = models.FloatField(null=True, blank=True, editable=False,
                                               verbose_name='Predicted number of size 0 fires.')

    risk_model_fires_size0_percentage = models.FloatField(null=True, blank=True, editable=False,
                                                          verbose_name='Percentage of size 0 fires.')

    risk_model_fires_size1 = models.FloatField(null=True, blank=True, editable=False,
                                               verbose_name='Predicted number of size 1 fires.')
    risk_model_fires_size1_percentage = models.FloatField(null=True, blank=True, editable=False,
                                                          verbose_name='Percentage of size 1 fires.')
    risk_model_fires_size2 = models.FloatField(null=True, blank=True, editable=False,
                                               verbose_name='Predicted number of size 2 firese.')
    risk_model_fires_size2_percentage = models.FloatField(null=True, blank=True, editable=False,
                                                          verbose_name='Percentage of size 2 fires.')
    population = models.IntegerField(null=True, blank=True, editable=False)
    population_class = models.IntegerField(null=True, blank=True, editable=False)
    featured = models.BooleanField(default=False, editable=False)
    dist_model_score_quartile = models.IntegerField()
    risk_model_deaths_quartile = models.IntegerField()
    risk_model_injuries_quartile = models.IntegerField()
    risk_model_fires_size0_quartile = models.IntegerField()
    risk_model_fires_size1_quartile = models.IntegerField()
    risk_model_fires_size2_quartile = models.IntegerField()
    risk_model_fires_quartile = models.IntegerField()
    risk_model_size1_percent_size2_percent_sum_quartile = models.IntegerField()
    risk_model_size1_percent_size2_percent_sum = models.FloatField(null=True, blank=True)
    risk_model_deaths_injuries_sum = models.FloatField(null=True, blank=True)
    risk_model_deaths_injuries_sum_quartile = models.IntegerField(null=True, blank=True)
    residential_fires_avg_3_years = models.FloatField(null=True, blank=True)
    residential_fires_avg_3_years_quartile = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'population_quartiles'


def refresh_quartile_view():
    with connections['default'].cursor() as cursor:
        cursor.execute('REFRESH MATERIALIZED VIEW population_quartiles;')


def create_quartile_views(sender, **kwargs):
    """
    Creates DB view based on quartile queries.
    """

    query = """
        SELECT
            (SELECT COALESCE(rm.risk_model_fires_size1_percentage,0)+COALESCE(rm.risk_model_fires_size2_percentage,0)) AS "risk_model_size1_percent_size2_percent_sum",
            (SELECT COALESCE(rm.risk_model_deaths,0)+COALESCE(rm.risk_model_injuries,0)) AS "risk_model_deaths_injuries_sum",
            fd."id",
            fd."created",
            fd."modified",
            fd."fdid",
            fd."name",
            fd."headquarters_address_id",
            fd."mail_address_id",
            fd."headquarters_phone",
            fd."headquarters_fax",
            fd."department_type",
            fd."organization_type",
            fd."website",
            fd."state",
            fd."region",
            fd."geom",
            rm."dist_model_score",
            rm."risk_model_deaths",
            rm."risk_model_injuries",
            rm."risk_model_fires",
            rm."risk_model_fires_size0",
            rm."risk_model_fires_size0_percentage",
            rm."risk_model_fires_size1",
            rm."risk_model_fires_size1_percentage",
            rm."risk_model_fires_size2",
            rm."risk_model_fires_size2_percentage",
            fd."population",
            fd."population_class",
            fd."featured",
            nfirs.avg_fires as "residential_fires_avg_3_years",
            rm."level",
            CASE WHEN (rm."risk_model_fires_size1_percentage" IS NOT NULL OR rm."risk_model_fires_size2_percentage" IS NOT NULL) THEN ntile(4) over (partition by COALESCE(rm.risk_model_fires_size1_percentage,0)+COALESCE(rm.risk_model_fires_size2_percentage,0) != 0, fd.population_class, rm.level order by COALESCE(rm.risk_model_fires_size1_percentage,0)+COALESCE(rm.risk_model_fires_size2_percentage,0)) ELSE NULL END AS "risk_model_size1_percent_size2_percent_sum_quartile",
            CASE WHEN (rm."risk_model_deaths" IS NOT NULL OR rm."risk_model_injuries" IS NOT NULL) THEN ntile(4) over (partition by COALESCE(rm.risk_model_deaths,0)+COALESCE(rm.risk_model_injuries,0) != 0, fd.population_class, rm.level order by COALESCE(rm.risk_model_deaths,0)+COALESCE(rm.risk_model_injuries,0)) ELSE NULL END AS "risk_model_deaths_injuries_sum_quartile",
            CASE WHEN rm."dist_model_score" IS NOT NULL THEN ntile(4) over (partition by rm.dist_model_score is not null, fd.population_class, rm.level order by rm.dist_model_score) ELSE NULL END AS "dist_model_score_quartile",
            CASE WHEN rm."risk_model_deaths" IS NOT NULL THEN ntile(4) over (partition by rm.risk_model_deaths is not null, fd.population_class, rm.level order by rm.risk_model_deaths) ELSE NULL END AS "risk_model_deaths_quartile",
            CASE WHEN rm."risk_model_injuries" IS NOT NULL THEN ntile(4) over (partition by rm.risk_model_injuries is not null, fd.population_class, rm.level order by rm.risk_model_injuries) ELSE NULL END AS "risk_model_injuries_quartile",
            CASE WHEN rm."risk_model_fires_size0" IS NOT NULL THEN ntile(4) over (partition by rm.risk_model_fires_size0 is not null, fd.population_class, rm.level order by rm.risk_model_fires_size0) ELSE NULL END AS "risk_model_fires_size0_quartile",
            CASE WHEN rm."risk_model_fires_size1" IS NOT NULL THEN ntile(4) over (partition by rm.risk_model_fires_size1 is not null, fd.population_class, rm.level order by rm.risk_model_fires_size1) ELSE NULL END AS "risk_model_fires_size1_quartile",
            CASE WHEN rm."risk_model_fires_size2" IS NOT NULL THEN ntile(4) over (partition by rm.risk_model_fires_size2 is not null, fd.population_class, rm.level order by rm.risk_model_fires_size2) ELSE NULL END AS "risk_model_fires_size2_quartile",
            CASE WHEN rm."risk_model_fires" IS NOT NULL THEN ntile(4) over (partition by rm.risk_model_fires is not null, fd.population_class, rm.level order by rm.risk_model_fires) ELSE NULL END AS "risk_model_fires_quartile",
            CASE WHEN "nfirs"."avg_fires" IS NOT NULL THEN ntile(4) over (partition by avg_fires is not null, fd.population_class, rm.level order by avg_fires) ELSE NULL END AS "residential_fires_avg_3_years_quartile"

        FROM "firestation_firedepartment" fd
        INNER JOIN "firestation_firedepartmentriskmodels" rm ON
            rm.department_id = fd.id
        LEFT JOIN (
            SELECT fire_department_id, AVG(count) as avg_fires, level
            from firestation_nfirsstatistic
            WHERE year >= 2010 and metric='residential_structure_fires'
            GROUP BY fire_department_id, level) nfirs
        ON (fd.id=nfirs.fire_department_id and nfirs.level = rm.level)
        WHERE archived=False
        """
    cursor = connections['default'].cursor()
    # Force materialied view recreation in case there are changes in the query
    print '(re)creating materialized view for "population_quartiles"'
    cursor.execute("DROP MATERIALIZED VIEW IF EXISTS population_quartiles;")
    cursor.execute("CREATE MATERIALIZED VIEW population_quartiles AS ({query});".format(query=query))


class NationalCalculations(models.Model):
    """
    National Calculations Views
    """

    id = models.OneToOneField(FireDepartment, db_column='id', primary_key=True)
    level = models.IntegerField(choices=HazardLevels.choices(), default=1)
    risk_model_size1_percent_size2_percent_sum_quartile = models.IntegerField(null=True, blank=True)
    risk_model_deaths_injuries_sum_quartile = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'national_calculations'


def refresh_national_calculations_view():
    with connections['default'].cursor() as cursor:
        cursor.execute('REFRESH MATERIALIZED VIEW national_calculations;')


def create_national_calculations_view(sender, **kwargs):
    """
    Creates DB view based on national calculations queries
    """

    query = """
        SELECT
            fs_fd.id,
            d.ntile1 AS risk_model_size1_percent_size2_percent_sum_quartile,
            d.ntile2 AS risk_model_deaths_injuries_sum_quartile,
            (SELECT {selected_level}) as level
        FROM firestation_firedepartment fs_fd,
        LATERAL(
            WITH
            results AS (
                SELECT fd."id", rm."dist_model_score", rm."level",
                    CASE
                        WHEN (rm."risk_model_fires_size1_percentage" IS NOT NULL
                            OR rm."risk_model_fires_size2_percentage" IS NOT NULL)
                        THEN
                            ntile(4) over (
                                partition BY COALESCE(
                                        rm.risk_model_fires_size1_percentage, 0
                                    ) + COALESCE(
                                        rm.risk_model_fires_size2_percentage, 0
                                    ) != 0, level
                                ORDER BY COALESCE(
                                        rm.risk_model_fires_size1_percentage, 0
                                    ) + COALESCE(
                                        rm.risk_model_fires_size2_percentage, 0
                                    )
                            )
                        ELSE NULL
                    END AS "risk_model_size1_percent_size2_percent_sum_quartile",
                    CASE
                        WHEN (rm."risk_model_deaths" IS NOT NULL
                            OR rm."risk_model_injuries" IS NOT NULL)
                        THEN ntile(4) over (
                            partition BY COALESCE(
                                rm.risk_model_deaths, 0
                            ) + COALESCE(
                                rm.risk_model_injuries, 0
                            ) != 0, level
                            ORDER BY
                                COALESCE(rm.risk_model_deaths, 0) +
                                COALESCE(rm.risk_model_injuries, 0)
                        )
                        ELSE NULL
                    END AS "risk_model_deaths_injuries_sum_quartile"
                FROM "firestation_firedepartment" fd
                INNER JOIN "firestation_firedepartmentriskmodels" rm on rm.department_id = fd.id
                WHERE rm."dist_model_score" IS NOT NULL and rm.level = {selected_level}
                ORDER BY fd."name" ASC
            ),
            row AS (
                SELECT *
                FROM results
                WHERE results.id=fs_fd.id
            ),
            all_data AS (
                SELECT
                    (SELECT ntile_results.ntile
                        FROM
                            (SELECT results.id,
                                ntile(4) over (ORDER BY results.dist_model_score ASC)
                            FROM results
                            INNER JOIN row
                            ON results.risk_model_size1_percent_size2_percent_sum_quartile =
                                row.risk_model_size1_percent_size2_percent_sum_quartile
                            ) AS ntile_results
                        WHERE ntile_results.id=fs_fd.id
                    ) as ntile1,
                    (SELECT ntile_results.ntile
                        FROM
                            (SELECT results.id,
                                ntile(4) over (ORDER BY results.dist_model_score ASC)
                            FROM results
                            INNER JOIN row
                            ON results.risk_model_deaths_injuries_sum_quartile =
                                row.risk_model_deaths_injuries_sum_quartile
                            ) AS ntile_results
                        WHERE ntile_results.id=fs_fd.id
                    ) as ntile2
            )
            select * from all_data where ntile1 IS NOT NULL OR ntile2 IS NOT NULL
        ) d
    """
    cursor = connections['default'].cursor()

    # Force materialied view recreation in case there are changes in the query
    print '(re)creating materialized view for "national_calculations"'
    cursor.execute("DROP MATERIALIZED VIEW IF EXISTS national_calculations;")
    complete_query = []
    for numlevel, level in FireDepartmentMetrics.RISK_LEVELS:
        complete_query.append(query.format(selected_level=numlevel))
    query = ' union '.join(complete_query)
    cursor.execute("CREATE MATERIALIZED VIEW national_calculations AS ({query});".format(query=query))


@deconstructible
class DocumentS3Storage(S3BotoStorage):
    pass


def document_upload_to(instance, filename):
    return 'departments/' + str(instance.department.pk) + '/' + filename


document_storage = DocumentS3Storage(bucket=settings.DOCUMENT_UPLOAD_BUCKET)
# Use the default storage backend in testing mode when the AWS key and token are not provided.
if settings.TESTING and not (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY):
    document_storage = None


class Document(models.Model):
    """
    Generic document for storing files uploaded by departments.
    """

    department = models.ForeignKey(FireDepartment, null=True, blank=True, on_delete=models.SET_NULL)
    filename = models.CharField(max_length=260, null=True, blank=True)
    file = models.FileField(storage=document_storage, upload_to=document_upload_to)
    created = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    def __unicode__(self):
        return '{0} uploaded by: {1} at {2}'.format(self.filename or '', self.uploaded_by or 'Unknown', self.created)


class DataFeedback(models.Model):
    """
    Model to store data feedback information.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    department = models.ForeignKey(FireDepartment, null=True, blank=True)
    firestation = models.ForeignKey(FireStation, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


reversion.register(FireStation)
reversion.register(FireDepartment)
reversion.register(Staffing)
