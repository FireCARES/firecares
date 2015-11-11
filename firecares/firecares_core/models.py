from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderQuotaExceeded
from jsonfield import JSONField
from time import sleep
from django.utils import timezone


class RecentlyUpdatedMixin(models.Model):
    """
    A mixin which adds a property that returns a boolean which represents if object was recently updated.
    """

    DAYS_CONSIDERED_RECENT = 10

    @property
    def recently_updated(self):
        try:
            diff = timezone.now() - self.modified
            return diff.days <= self.DAYS_CONSIDERED_RECENT
        except:
            return False

    class Meta:
        abstract = True


class Country(models.Model):
    """Model for countries"""
    iso_code = models.CharField(max_length=2, primary_key=True)
    name = models.CharField(max_length=45, blank=False)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Countries"
        ordering = ["name", "iso_code"]


class Address(models.Model):
    """
    Model to store addresses
    """
    address_line1 = models.CharField("Address line 1", max_length=100)
    address_line2 = models.CharField("Address line 2", max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=False)
    state_province = models.CharField("State/Province", max_length=40, blank=True)
    postal_code = models.CharField("Postal Code", max_length=10)
    country = models.ForeignKey(Country, blank=False)
    geom = models.PointField(null=True, blank=True)
    objects = models.GeoManager()
    geocode_results = JSONField(null=True, blank=True)

    def get_row_display(self):
        return '{city}, {state_province}, {postal_code}' \
            .format(address_line1=self.address_line1, address_line2=self.address_line2, city=self.city,
                    state_province=self.state_province, postal_code=self.postal_code, country=self.country.iso_code)

    def get_full_display(self):
        return '{line1}{line2}, {city}, {state_province}, {postal_code}' \
            .format(line1=self.address_line1, line2=' ' + self.address_line2 if self.address_line2 else '', city=self.city,
                    state_province=self.state_province, postal_code=self.postal_code, country=self.country.iso_code)

    @classmethod
    def create_from_string(cls, query_string, dry_run=False):
        g = GoogleV3()
        try:
            results = g.geocode(query=query_string)
        except GeocoderQuotaExceeded:
            sleep(0.5)
            results = g.geocode(query=query_string)

        if results and results.latitude and results.longitude:
            params = dict(geom=Point(results.longitude, results.latitude))
            filter_components = lambda n: [c for c in results.raw['address_components'] if n in c['types']]
            postal_codes = filter_components('postal_code')
            countries = filter_components('country')
            states = filter_components('administrative_area_level_1')
            cities = filter_components('locality')
            street_numbers = filter_components('street_number')
            street_names = filter_components('route')

            if postal_codes:
                params['postal_code'] = postal_codes[0]['short_name']

            if countries:
                params['country'] = Country.objects.get(iso_code=countries[0]['short_name'])

            if states:
                params['state_province'] = states[0]['short_name']

            if cities:
                params['city'] = cities[0]['long_name']

            if street_numbers and street_names:
                params['address_line1'] = '{0} {1}'.format(street_numbers[0]['short_name'], street_names[0]['short_name'])

            if not dry_run:
                try:
                    objs = cls.objects.get(**params)
                except cls.DoesNotExist:
                    objs = cls.objects.create(**params)
                return objs
            else:
                print 'Create new address with these parameters: {0}'.format(params)
                return cls(**params)


    def geocode(self):
        g = GoogleV3()
        query_string = self.get_row_display()
        try:
            results = g.geocode(query=query_string)
        except GeocoderQuotaExceeded:
            sleep(0.5)
            results = g.geocode(query=query_string)

        if results and results.latitude and results.longitude:
            self.geom = Point(results.longitude, results.latitude)
            self.geocode_results = results.raw
            self.save()

    @classmethod
    def batch_geocode(cls):
        for row in cls.objects.filter(geom__isnull=True, geocode_results__isnull=True):
            print row.get_row_display()
            row.geocode()

    def __unicode__(self):
        return "%s, %s %s" % (self.city, self.state_province,
                              str(self.country))

    class Meta:
        verbose_name_plural = "Addresses"
        unique_together = ("address_line1", "address_line2", "postal_code",
                           "city", "state_province", "country")
