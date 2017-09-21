import mock
import requests
import json
import os

from django.test import TestCase, Client
from django.contrib.gis.geos import Point, MultiPolygon,LinearRing, Polygon
from django.contrib.gis.geos import fromstr

from firecares.weather.models import WeatherWarnings, DepartmentWarnings


class WeatherWarningTests(TestCase):


    def load_mock_warning(self, filename):
        
        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as f:
            return f.read()


    def test_add_warning_department(self):
        """
        Tests the loading of Warning and validity of department warning
        """

        warningjson = json.loads(self.load_mock_warning('mock_warning.json'))

        #Convert Geometry
        poly = map(LinearRing, warningjson['feature']['geometry']['rings'])
        warninggeom = MultiPolygon(fromstr(str(Polygon(*poly))),)


        warningobj = {}
        warningobj['url'] = warningjson['feature']['attributes']['url']
        warningobj['warnid'] = warningjson['feature']['attributes']['warnid']
        warningobj['prod_type'] = warningjson['feature']['attributes']['prod_type']
        warningobj['warngeom'] = warninggeom

        departwarnobj = {}
        departwarnobj['url'] = warningjson['feature']['attributes']['url']
        departwarnobj['warngeom'] = warninggeom
        departwarnobj['warningname'] = warningjson['feature']['attributes']['prod_type']
        departwarnobj['departmentfdid'] = "23645",
        departwarnobj['warningfdid'] = warningjson['feature']['attributes']['warnid']

        createwarning = WeatherWarnings.create_warning(warningobj)
        createdeptwarning = DepartmentWarnings.create_dept_warning(departwarnobj)

        self.assertEqual(createwarning.warnid, warningjson['feature']['attributes']['warnid'])

        #Tests to check if loaded to department warning
        self.assertEqual(createdeptwarning.warningfdid, warningjson['feature']['attributes']['warnid'])


    def test_warning_service(self):
        """
        Tests the weather URL and response
        """

        response = requests.get('https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/query?'
                        'where=objectId<5&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false'
                        '&returnTrueCurves=false&outSR=&returnIdsOnly=true&returnCountOnly=false&returnZ=false&returnM=false&returnDistinctValues=false&f=json')


        warnings = set(json.loads(response.content)['objectIds'])

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(warnings)>-1)
    
