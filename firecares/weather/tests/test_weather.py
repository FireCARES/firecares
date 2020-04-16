import json
import os

from django.test import TestCase
from requests_mock import Mocker
from django.contrib.gis.geos import MultiPolygon, LinearRing, Polygon
from django.contrib.gis.geos import fromstr
from firecares.weather.models import WeatherWarnings, DepartmentWarnings
from firecares.firestation.models import FireDepartment


@Mocker()
class WeatherWarningTests(TestCase):

    def setUp(self):

        self.service_warning_objids = 'https://idpgis.ncep.noaa.gov/arcgis/rest/services/NWS_Forecasts_Guidance_Warnings/watch_warn_adv/MapServer/1/query?where=objectid<10&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=false&returnTrueCurves=false&outSR=&returnIdsOnly=true&returnCountOnly=false&returnZ=false&returnM=false&returnDistinctValues=false&f=json'

    def load_mock_warning(self, filename):

        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as f:
            return f.read()

    def test_add_warning_department(self, mock):
        """
        Tests the loading of Warning and validity of department warning
        """
        warningjson = json.loads(self.load_mock_warning('mock_warning.json'))

        #  Convert Geometry
        poly = map(LinearRing, warningjson['feature']['geometry']['rings'])
        warninggeom = MultiPolygon(fromstr(str(Polygon(*poly))),)

        warningobj = {}
        warningobj['url'] = warningjson['feature']['attributes']['url']
        warningobj['warnid'] = warningjson['feature']['attributes']['warnid']
        warningobj['prod_type'] = warningjson['feature']['attributes']['prod_type']
        warningobj['warngeom'] = warninggeom

        createwarning = WeatherWarnings.create_warning(warningobj)

        intersectdepartment = FireDepartment.objects.filter(fdid="80343")

        departwarnobj = {}
        departwarnobj['url'] = warningjson['feature']['attributes']['url']
        departwarnobj['warngeom'] = warninggeom
        departwarnobj['department'] = intersectdepartment
        departwarnobj['warningname'] = warningjson['feature']['attributes']['warnid']
        departwarnobj['prod_type'] = warningjson['feature']['attributes']['prod_type']
        departwarnobj['departmentfdid'] = "80343"
        departwarnobj['warningfdid'] = createwarning

        createdeptwarning = DepartmentWarnings.create_dept_warning(departwarnobj)

        self.assertEqual(createwarning.warnid, warningjson['feature']['attributes']['warnid'])

        #  Tests to check if loaded to department warning
        self.assertEqual(createdeptwarning.warningname, warningjson['feature']['attributes']['warnid'])

    def setup_mock_warningobjectids(self, mock):

        mock.get(self.service_warning_objids, text=self.load_mock_warning('warningobjectIds.json'))

    def test_warning_service(self, mock):
        """
        Tests the weather URL and response
        """
        self.setup_mock_warningobjectids(mock)

        warningjson = json.loads(self.load_mock_warning('warningobjectIds.json'))

        warningobjectids = warningjson['objectIds']

        self.assertTrue(len(warningobjectids) > -1)
