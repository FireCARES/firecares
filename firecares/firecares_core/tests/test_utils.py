from django.contrib.gis.geos import Point
from django.test import TestCase
from firecares.firecares_core.models import Address, Country
from firecares.firestation.models import FireStation
from firecares.utils import lenient_summation, lenient_mean, get_property


class TestUtilityFunctions(TestCase):
    def test_permissive_functions(self):
        # Tests that the permissive functions perform correctly
        self.assertEqual(lenient_summation(1, 2, 3), 6)
        self.assertEqual(lenient_summation(1, None, 3), 4)
        self.assertEqual(lenient_summation(), None)
        self.assertEqual(lenient_summation(0), 0)
        # Make sure that mapping functions work correctly
        d = {'max': 1}
        d2 = {'max': 2}
        self.assertEqual(lenient_summation(None, d, d2, mapping=lambda x: x['max'] if x else None), 3)

        self.assertEqual(lenient_mean(1, 2, 3), 2)
        self.assertEqual(lenient_mean(1, None, 2), 1.5)
        self.assertEqual(lenient_mean(None, None, None), None)
        self.assertEqual(lenient_mean(0), 0)
        # Make sure that mapping functions work correctly
        d = {'avg': 1.5}
        d2 = {'avg': 2.5}
        self.assertEqual(lenient_mean(None, d, d2, mapping=lambda x: x['avg'] if x else None), 2)

    def test_nested_property_retrieval(self):
        c = Country.objects.create(iso_code='US', name='\'Merica')
        addr = Address.objects.create(address_line1='Line1', country=c, geom=Point(-118.42170426600454, 34.09700463377199))
        fs = FireStation.objects.create(name='TEST FS', station_address=addr, geom=Point(-118.42170426600454, 34.09700463377199))

        self.assertEqual(get_property(fs, 'name'), 'TEST FS')
        self.assertEqual(get_property(fs, 'station_address.address_line1'), 'Line1')
        self.assertEqual(get_property(fs, 'station_address.country.name'), '\'Merica')
        self.assertEqual(get_property(fs, 'station_address.address_line1.upper'), 'LINE1')
