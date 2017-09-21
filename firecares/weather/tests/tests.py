
import mock
import requests
import json
from django.test import TestCase
from django.test.client import Client

from firecares.weather.models import WeatherWarnings


class WeatherWarningTests(TestCase):

	def test_warning_service(self):
        """
        Tests the weather URL
        """
                response = requests.get('https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/query?'
                        'where=objectId<5&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false'
                        '&returnTrueCurves=false&outSR=&returnIdsOnly=true&returnCountOnly=false&returnZ=false&returnM=false&returnDistinctValues=false&f=json')


                response = json.loads(objects.content)['objectIds']

                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.is_valid())


        def test_add_warning(self):
        """
        Test the warning adding to database
        TODO
        """
                self.assertEqual(1,1)
                #self.assertTrue(response.is_valid())


        def test_check_department_warning(self):
        """
        Test the intersection with warning and departments
        TODO
        """
                
                #WeatherWarnings.add_warnings_to_departments(departmentList, warningGemoetry)
               

                self.assertEqual(1,1)
                #self.assertTrue(response.is_valid())