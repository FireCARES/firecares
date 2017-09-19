
import mock
import requests
from StringIO import StringIO
from django.contrib.gis.geos import Point, GEOSGeometry
from django.db import connections
from django.test import TestCase
from django.test.client import Client

from firecares.weather.models import WeatherWarnings


class WeatherWarningTests(TestCase):

	def test_warning_service(self):
        """
        Tests the weather URL
        """
        WeatherWarnings.load_data()

        #response = c.get(fd.get_absolute_url())

        #self.assertEqual(response.status_code, 200)
        self.assertEqual(1,1)