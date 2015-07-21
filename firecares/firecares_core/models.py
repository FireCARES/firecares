from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from geopy.geocoders import GoogleV3
from geopy.exc import GeocoderQuotaExceeded
from jsonfield import JSONField
from time import sleep


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
        return '{city}, {state_provice}, {postal_code}' \
            .format(address_line1=self.address_line1, address_line2=self.address_line2, city=self.city,
                    state_provice=self.state_province, postal_code=self.postal_code, country=self.country.iso_code)

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
