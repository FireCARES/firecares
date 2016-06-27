import json
import os
import requests
import string
from .forms import StaffingForm
from .models import FireDepartment, FireStation, Staffing, PopulationClass9Quartile
from django.db import connections
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.core import mail
from django.core.cache import caches
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.urlresolvers import reverse, resolve
from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from django.contrib.auth import get_user_model
from firecares.usgs.models import UnincorporatedPlace, MinorCivilDivision
from firecares.firecares_core.models import Address, Country
from firecares.firecares_core.mixins import hash_for_cache
from firecares.firestation.models import create_quartile_views, Document
from firecares.firestation.templatetags.firecares import quartile_text, risk_level
from firecares.firestation.managers import CalculationsQuerySet
from urlparse import urlsplit, urlunsplit
from reversion.models import Revision
from reversion import revisions as reversion
from firecares.importers import GeoDjangoImport
from firecares.tasks.quality_control import test_all_departments_urls

User = get_user_model()


class FireStationTests(TestCase):

    def test_firestation_website_links(self):
        FireDepartment.objects.create(name='Good', website='http://www.google.com')
        test_all_departments_urls()
        self.assertTrue(len(mail.outbox) == 0, "email sent to admin with errors")
        FireDepartment.objects.create(name='Bad', website='www.mawebsith.com')
        test_all_departments_urls()
        self.assertTrue(len(mail.outbox) == 1, "email not sent to admin with errors")

    def setUp(self):
        self.response_capability_enabled = True
        self.current_api_version = 'v1'
        self.fire_station = self.create_firestation()

        self.username = 'admin'
        self.password = 'admin'
        self.user, created = User.objects.get_or_create(username=self.username, is_superuser=True)

        if created:
            self.user.set_password(self.password)
            self.user.save()

        self.non_admin = 'non_admin'
        self.non_admin_password = 'non_admin'
        self.non_admin_user, created = User.objects.get_or_create(username=self.non_admin)

        if created:
            self.non_admin_user.set_password(self.non_admin_password)
            self.non_admin_user.save()

    def assert_redirect_to_login(self, response):
        self.assertEqual(response.status_code, 302)
        split = urlsplit(response.url)
        shimmed = urlsplit(urlunsplit((split.scheme, split.netloc, split.path + '/', split.query, split.fragment)))
        self.assertEqual(resolve(shimmed.path).url_name, 'login')

    def create_firestation(self, **kwargs):
        return FireStation.objects.create(station_number=25, name='Test Station', geom=Point(35, -77),
                                          **kwargs)

    def test_firestation_detail_page_requires_login(self):
        """
        Ensures that the firestation detail page redirects to login for unauthoized users
        """

        call_command('loaddata', 'firecares/firestation/fixtures/test_firestation_detail.json')

        c = Client()

        fs = FireStation.objects.filter(id=46971).first()

        # Make sure that we're redirected to login since we're not yet authenticated
        response = c.get(reverse('firestation_detail', args=[fs.pk]))
        self.assert_redirect_to_login(response)
        response = c.get(reverse('firestation_detail_slug', args=[fs.pk, fs.slug]))
        self.assert_redirect_to_login(response)

        c.login(**{'username': 'admin', 'password': 'admin'})

        # Make sure that we get back a valid page for both the regular route + slug route
        response = c.get(reverse('firestation_detail', args=[fs.pk]))
        self.assertEqual(response.status_code, 200)
        # Ensure that the slug works as well
        response = c.get(reverse('firestation_detail_slug', args=[fs.pk, fs.slug]))
        self.assertEqual(response.status_code, 200)

    def test_authentication(self):
        """
        Tests users have to be authenticated to GET resources.
        """

        c = Client()

        for resource in ['staffing', 'firestations']:
            url = '{0}?format=json'.format(reverse('api_dispatch_list', args=[self.current_api_version, resource]),)
            response = c.get(url)
            self.assertEqual(response.status_code, 401)

            c.login(**{'username': 'admin', 'password': 'admin'})
            response = c.get(url)
            self.assertEqual(response.status_code, 200)
            c.logout()

    def test_add_capability_to_station(self):
        """
        Tests adding a capability via the API.
        """

        url = '{0}?format=json'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'staffing']),)
        station_uri = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                                       self.fire_station.id)
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        capability = dict(id=2,  # shouldn't have to put the id here
                          firestation=station_uri,
                          personnel=4,
                          apparatus='Boat'
                          )

        response = c.post(url, data=json.dumps(capability), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.fire_station.staffing_set.all().count(), 1)

        unit = self.fire_station.staffing_set.all()[0]
        self.assertEqual(unit.personnel, 4)
        self.assertEqual(unit.apparatus, 'Boat')

    def test_update_capability(self):
        """
        Tests updating the capability through the API.
        """

        capability = Staffing.objects.create(firestation=self.fire_station, personnel=4, apparatus='Boat')

        url = '{0}{1}/?format=json'.format(reverse('api_dispatch_list',
                                                   args=[self.current_api_version, 'staffing']), capability.id)

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        params = dict(personnel=4, apparatus='Engine')

        response = c.put(url, data=json.dumps(params), content_type='application/json')
        # Since the API is returning data, it'll pass a 200 vs 204
        self.assertEqual(response.status_code, 200)

        updated_capability = Staffing.objects.get(id=capability.id)
        self.assertEqual(updated_capability.personnel, 4)
        self.assertEqual(updated_capability.apparatus, 'Engine')

    def test_deleting_a_capability(self):
        """
        Tests deleting the capability through the API.
        """

        capability = Staffing.objects.create(firestation=self.fire_station, personnel=4)

        url = '{0}{1}/?format=json'.format(reverse('api_dispatch_list',
                                                   args=[self.current_api_version, 'staffing']), capability.id)

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        response = c.delete(url)
        self.assertEqual(response.status_code, 204)

        # make sure it actually deleted the object.
        with self.assertRaises(Staffing.DoesNotExist):
            Staffing.objects.get(id=capability.id)

    def test_response_capability_form_validation(self):
        """
        Tests capability validation via a Form object.
        """

        capability = dict(firestation=self.fire_station.id,
                          personnel='test'
                          )

        rc = StaffingForm(capability)
        for key in capability.keys():
            if key not in ['firestation']:
                self.assertTrue(key in rc.errors, 'The invalid field:{0} was not returned in the error message.'
                                .format(key))

    def test_add_capability_validation(self):
        """
        Tests capability validation via the API.
        """

        url = '{0}?format=json'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'staffing']),)
        station_uri = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                                       self.fire_station.id)
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        capability = dict(id=2,  # shouldn't have to put the id here
                          firestation=station_uri,
                          personnel='test',
                          apparatus='whatever'
                          )

        response = c.post(url, data=json.dumps(capability), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        for key in capability.keys():
            if key not in ['firestation', 'id']:
                self.assertTrue(key in response.content, 'The invalid field:{0} was not returned in the error message.'
                                .format(key))

    def test_filter_capability_by_fire_station(self):
        """
        Tests filtering response capabilities by the fire station.
        """

        url = '{0}?format=json&firestation={1}'.format(reverse('api_dispatch_list',
                                                               args=[self.current_api_version, 'staffing']),
                                                       self.fire_station.id
                                                       )
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})
        response = c.get(url)
        self.assertEqual(response.status_code, 200)

    def test_deleting_a_fire_station(self):
        """
        Tests that DELETE requests through the API return a 405 (not supported).
        """

        url = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                                       self.fire_station.id)
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        response = c.delete(url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(FireStation.objects.get(id=self.fire_station.id))

    def test_get_population_class(self):
        """
        Tests the population class logic.
        """
        fd = FireDepartment.objects.create(name='Test db', population=0)
        self.assertEqual(fd.get_population_class(), 0)

        fd.population = 2500
        self.assertEqual(fd.get_population_class(), 1)

        fd.population = 9999
        self.assertEqual(fd.get_population_class(), 2)

        fd.population = 15000
        self.assertEqual(fd.get_population_class(), 3)

        fd.population = 25001
        self.assertEqual(fd.get_population_class(), 4)

        fd.population = 99999
        self.assertEqual(fd.get_population_class(), 5)

        fd.population = 100000
        self.assertEqual(fd.get_population_class(), 6)

        fd.population = 499999
        self.assertEqual(fd.get_population_class(), 7)

        fd.population = 500000
        self.assertEqual(fd.get_population_class(), 8)

        fd.population = 999999
        self.assertEqual(fd.get_population_class(), 8)

        fd.population = 1000001
        self.assertEqual(fd.get_population_class(), 9)

    def test_population_metrics_table(self):
        """
        Ensure the population_metrics_table method returns expected results.
        """

        fd = FireDepartment.objects.create(name='Test db', population=0)

        for i in range(0, 10):
            fd.population_class = i
            self.assertIsNotNone(fd.population_metrics_table)

        fd.population_class = 11
        self.assertIsNone(fd.population_metrics_table)

    def test_department_detail_view_requires_login(self):
        """
        Ensures the department pages require login.
        Note: This is just until we are out of closed beta.
        """

        fd = FireDepartment.objects.create(name='Test db', population=0)
        c = Client()
        response = c.get(fd.get_absolute_url())
        self.assert_redirect_to_login(response)

    def test_department_list_view_requires_login(self):
        """
        Ensures the department list view requires login.
        Note: This is just until we are out of closed beta.
        """

        fd = FireDepartment.objects.create(name='Test db', population=0)
        c = Client()
        response = c.get('/departments')
        self.assert_redirect_to_login(response)

    def test_convenience_methods(self):
        """
        Make sure the size2_and_greater_percentile_sum and deaths_and_injuries_sum methods do not throw errors.
        """
        fd = FireDepartment.objects.create(name='Test db',
                                           population=0,
                                           population_class=1,
                                           department_type='test')

        self.assertIsNone(fd.size2_and_greater_percentile_sum)
        self.assertIsNone(fd.deaths_and_injuries_sum)

        fd.risk_model_deaths = 1
        self.assertEqual(fd.deaths_and_injuries_sum, 1)

        fd.risk_model_injuries = 1
        self.assertEqual(fd.deaths_and_injuries_sum, 2)

        fd.risk_model_fires_size1_percentage = 1
        self.assertEqual(fd.size2_and_greater_percentile_sum, 1)

        fd.risk_model_fires_size2_percentage = 1
        self.assertEqual(fd.size2_and_greater_percentile_sum, 2)

    def test_population_metric_views(self):
        """
        Tests the population metric views.
        """
        fd = FireDepartment.objects.create(name='Test db',
                                           population=0,
                                           population_class=9,
                                           department_type='test')

        # update materialized view manually after adding new record
        cursor = connections['default'].cursor()
        cursor.execute("REFRESH MATERIALIZED VIEW population_class_9_quartiles;")

        self.assertTrue(PopulationClass9Quartile.objects.get(id=fd.id))

        # make sure the population class logic works
        self.assertTrue(fd.population_class_stats)

        # make sure the department page does not return an error
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})
        response = c.get(fd.get_absolute_url())

        self.assertEqual(response.status_code, 200)

    def test_quartile_text(self):
        """
        Tests the quartile text template tag.
        """
        self.assertEqual('lowest', quartile_text(1))
        self.assertEqual('second lowest', quartile_text(2))
        self.assertEqual('second highest', quartile_text(3))
        self.assertEqual('highest', quartile_text(4))
        self.assertIsNone(quartile_text(5))

    def test_risk_level(self):
        """
        Tests the quartile text template tag.
        """
        self.assertEqual('low', risk_level(1))
        self.assertEqual('medium', risk_level(2))
        self.assertEqual('medium', risk_level(3))
        self.assertEqual('high', risk_level(4))
        self.assertIsNone(risk_level(5))

    def test_performance_model_urls(self):
        """
        Make HEAD requests to ensure external sites work.
        """

        urls = [
            'http://www.nist.gov/el/fire_research/upload/Report-on-Residential-Fireground-Field-Experiments.pdf',  # NIST TN 1661
            'http://www.nfpa.org/codes-and-standards/document-information-pages?mode=code&code=1710'  # NFPA 1710
        ]

        for url in urls:
            response = requests.head(url, allow_redirects=True)
            self.assertEqual(response.status_code, 200, 'Url: {0} did not return a 200.'.format(url))

        get_urls = [
            'http://nvlpubs.nist.gov/nistpubs/TechnicalNotes/NIST.TN.1797.pdf',  # NIST TN 1797
        ]

        # Hack to get around fact that nist.gov returns a 404 for HEAD requests to the NIST.TN.1797.pdf, but a 200 for GETs :/
        for url in get_urls:
            response = requests.get(url, headers={'Range': 'bytes=0-0'})
            self.assertEqual(response.status_code, 206, 'Url: {0} did not return a 206.'.format(url))

    def test_fts_functions_exist(self):
        """
        Ensures the Full Text Search functions exist.
        """

        cursor = connections['default'].cursor()
        cursor.execute("select specific_name from information_schema.routines where specific_name like 'department_fts_document%%';")
        self.assertEqual(len(cursor.fetchall()), 3)

    def test_fts_triggers_exist(self):
        """
        Ensures the Full Text Search triggers exist.
        """

        cursor = connections['default'].cursor()
        # Ensure fts update trigger exists
        cursor.execute("select trigger_name from information_schema.triggers where trigger_name='department_fts_update_trigger'")
        self.assertEqual(len(cursor.fetchall()), 1)

        # Ensure fts insert trigger exists
        cursor.execute("select trigger_name from information_schema.triggers where trigger_name='department_fts_insert_trigger'")
        self.assertEqual(len(cursor.fetchall()), 1)

    def test_full_text_search_insert_trigger(self):
        """
        Tests the insert trigger for Full Text Search.
        """

        FireDepartment.objects.create(name='Test db',
                                      population=0,
                                      population_class=9,
                                      department_type='test',
                                      state='VA')


        dep = FireDepartment.objects.all().extra(select={'val':'select fts_document from firestation_firedepartment a where a.id=firestation_firedepartment.id'})
        self.assertEqual(dep[0].val, "'db':2 'test':1 'va':3")

    def test_full_text_search_update_trigger(self):
        """
        Tests the insert trigger for Full Text Search.
        """
        fd = FireDepartment.objects.create(name='Test db', population=0, population_class=9, department_type='test',
                                           state='VA')

        fts_query = 'select fts_document from firestation_firedepartment a where a.id=firestation_firedepartment.id'

        dep = FireDepartment.objects.all().extra(select={'vector': fts_query})
        vector = dep[0].vector

        fd.name = 'New york'
        fd.save()

        dep = FireDepartment.objects.all().extra(select={'vector': fts_query})
        self.assertNotEqual(vector, dep[0].vector)

    def test_full_text_search_method(self):
        """
        Tests the Full Text Search method on the FireDepartment object.
        """

        rfd = FireDepartment.objects.create(name='Richmond', population=0, population_class=9, state='VA')
        lafd = FireDepartment.objects.create(name='Los Angeles', population=0, population_class=9, state='CA')

        results = FireDepartment.objects.all().full_text_search('Ca')
        self.assertTrue(lafd in results)
        self.assertFalse(rfd in results)

        results = FireDepartment.objects.all().full_text_search('Ca|va')
        self.assertTrue(lafd in results)
        self.assertTrue(rfd in results)

    def test_sanitize_fts_term(self):
        """
        Tests the logic to sanitize full text search terms.
        """
        sanitize = CalculationsQuerySet._sanitize_full_text_search

        # Test escaping single-quotes
        self.assertEqual(sanitize("'Testing'"), "''Testing''")

        # Test replacing double-quotes with single quotes
        self.assertEqual(sanitize('"Testing"'), "''Testing''")

        # Test replacing double-quotes with single quotes
        self.assertEqual(sanitize('Test  double spaces.'), "Test:* & double:* & spaces:*")

        # Test punctuation (!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~) stripping
        self.assertEqual(sanitize(string.punctuation), "'' &'' & |")

    def test_department_list_with_fts(self):
        """
        Tests the departments list view with FTS search.
        """

        lafd = FireDepartment.objects.create(name='Los Angeles', population=0, population_class=9, state='CA')
        rfd = FireDepartment.objects.create(name='Richmond', population=0, population_class=9, state='VA')

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})
        response = c.get(reverse('firedepartment_list'), {'q': 'Ca'})
        self.assertTrue(lafd in response.context['object_list'])
        self.assertFalse(rfd in response.context['object_list'])

        response = c.get(reverse('firedepartment_list'), {'q': '', 'state':'CA'})
        self.assertTrue(lafd in response.context['object_list'])

    def test_generate_thumbnail_url(self):
        """
        Tests the generate thumbnail url logic.
        """

        lafd = FireDepartment.objects.create(name='Los Angeles', population=0, population_class=9, state='CA')

        # with no geometry make sure the thumbnail is the place holder
        self.assertEqual(lafd.generate_thumbnail(), '/static/firestation/theme/assets/images/content/property-1.jpg')
        lafd_poly = Polygon.from_bbox((-118.42170426600454, 34.09700463377199, -118.40170426600453,  34.117004633771984))

        us = Country.objects.create(iso_code='US', name='United States')
        address = Address.objects.create(address_line1='Test', country=us, geom=Point(-118.42170426600454, 34.09700463377199))
        lafd.headquarters_address = address
        lafd.save()

        # ensure a fd with no geometry uses the headquarters address location
        self.assertEqual(lafd.generate_thumbnail(), 'http://api.tiles.mapbox.com/v4/garnertb.mmlochkh/pin-l-embassy+0074D9(-118.421704266,34.0970046338)/-118.421704266,34.0970046338,8/500x300.png?access_token={0}'.format(settings.MAPBOX_ACCESS_TOKEN))

        # ensure a fd with a geometry uses the centroid of the geometry
        lafd.geom = MultiPolygon([lafd_poly])
        self.assertEqual(lafd.generate_thumbnail(), 'http://api.tiles.mapbox.com/v4/garnertb.mmlochkh/pin-l-embassy+0074D9(-118.411704266,34.1070046338)/-118.411704266,34.1070046338,8/500x300.png?access_token={0}'.format(settings.MAPBOX_ACCESS_TOKEN))

        # ensure the marker is not in the url when marker=False
        self.assertEqual(lafd.generate_thumbnail(marker=False), 'http://api.tiles.mapbox.com/v4/garnertb.mmlochkh/False-118.411704266,34.1070046338,8/500x300.png?access_token={0}'.format(settings.MAPBOX_ACCESS_TOKEN))

    def test_department_list_view(self):
        """
        Tests the list view.
        """

        fd = FireDepartment.objects.create(name='Adak Volunteer Fire Department', population=None)
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        # regression test default params do not filter out the object
        response = c.get('/departments?name=adak&state=&region=&fdid=&sortBy=&limit=')
        self.assertTrue(fd in response.context['object_list'])

        # regression test default params do not filter out the object
        response = c.get('/departments?fdid=&state=&name=adak&region=&population=0+%2C+9818605&q=&dist_model_score=0+%2C+458&sortBy=&limit=')
        self.assertTrue(fd in response.context['object_list'])

        # test limit=0 does not throw a 500
        response = c.get('/departments?fdid=&state=&name=adak&region=&population=0+%2C+9818605&q=&dist_model_score=0+%2C+458&sortBy=&limit=0')
        self.assertTrue(fd in response.context['object_list'])

        # test strings in the numeric fields don't throw a 500
        response = c.get('/departments?fdid=&state=&name=adak&region=&population=wer0+%2C+9818605&q=&dist_model_score=we0+%2C+458&sortBy=&limit=0')
        self.assertTrue(fd in response.context['object_list'])

    def test_similar_list_view(self):
        """
        Tests the similar departments list view.
        """
        fd = FireDepartment.objects.create(name='Adak Volunteer Fire Department', population=5000)
        blueFD = FireDepartment.objects.create(name='Blue Volunteer Fire Department', population=5100)
        unrelated = FireDepartment.objects.create(name='Unrelated Fire Department', population=15000000)

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        response = c.get(reverse('similar_departments_slug', args=[fd.id, fd.slug]))
        self.assertTrue(blueFD in response.context['object_list'])
        self.assertTrue(fd not in response.context['object_list'])
        self.assertTrue(unrelated not in response.context['object_list'])
        self.assertEqual(response.status_code, 200)

        response = c.get(reverse('similar_departments', args=[123]))
        self.assertEqual(response.status_code, 404)

    def test_update_government_unit_associations(self):
        """
        Tests functionality associated with updating a FireDepartment's associated government units
        """

        call_command('loaddata', 'firecares/firestation/fixtures/test_government_unit_association.json')

        fd = FireDepartment.objects.get(pk=86610)
        place = UnincorporatedPlace.objects.get(pk=9254)
        div = MinorCivilDivision.objects.get(pk=31575)

        c = Client()
        response = c.get(reverse('firedepartment_update_government_units', args=[fd.pk]))

        # Make sure that we're redirected to login since we're not yet authenticated
        self.assert_redirect_to_login(response)

        # Login and make sure that we get a 200 back from the govt unit association update page
        c.login(**{'username': 'admin', 'password': 'admin'})
        response = c.get(reverse('firedepartment_update_government_units', args=[fd.pk]))
        self.assertEqual(response.status_code, 200)

        old_point_count = fd.geom.num_points
        response = c.post(reverse('firedepartment_update_government_units', args=[fd.pk]), {'unincorporated_places': [place.pk]})
        self.assertRedirects(response, reverse('firedepartment_detail_slug', args=[fd.pk, fd.slug]), fetch_redirect_response=False)
        # Make sure that the UnincorporatedPlace is associated
        self.assertEqual(fd.government_unit.first().object, place)

        # Update the geom for the FD
        response = c.post(reverse('firedepartment_update_government_units', args=[fd.pk]), {'minor_civil_divisions': [div.pk], 'update_geom': [1]})

        # Should have a different point count now that geometries are merged
        fd.refresh_from_db()
        self.assertNotEqual(fd.geom.num_points, old_point_count)

        # Test for ability to create new geoms for FireDepartments that didn't previously have a geometry
        fd_null_geom = FireDepartment.objects.get(pk=96582)
        div2 = MinorCivilDivision.objects.get(pk=19336)

        response = c.get(reverse('firedepartment_update_government_units', args=[fd_null_geom.pk]))
        self.assertEqual(response.status_code, 200)
        response = c.post(reverse('firedepartment_update_government_units', args=[fd_null_geom.pk]), {'minor_civil_divisions': [div2.pk], 'update_geom': [1]})
        self.assertRedirects(response, reverse('firedepartment_detail_slug', args=[fd_null_geom.pk, fd_null_geom.slug]), fetch_redirect_response=False)

    def test_firedepartment_detail_page_caching(self):
        # Requires having something *other* than the DummyCache in order test caching
        call_command('loaddata', 'firecares/firestation/fixtures/test_government_unit_association.json')
        # need to create the quartile views in order for the dept detail page to be retrieved
        create_quartile_views(None)

        c = Client()
        fd = FireDepartment.objects.get(pk=86610)

        # Login and make sure that we get a 200 back from the govt unit association update page
        c.login(**{'username': 'admin', 'password': 'admin'})
        response = c.get(reverse('firedepartment_update_government_units', args=[fd.pk]))
        self.assertEqual(response.status_code, 200)

        cache = caches['default']
        # remove cached items from other test runs
        cache.clear()
        response = c.get(reverse('firedepartment_detail', args=[fd.pk]))
        prefix = hash_for_cache('firestation.change_firedepartment:True', '/departments/86610')
        keys = cache._cache.keys()
        self.assertTrue(any([prefix in x for x in keys]))

        # prime the cache with a slugged page path that is very long
        response = c.get(reverse('firedepartment_detail_slug', args=[fd.pk, fd.slug]))
        c.logout()

        # tester_mcgee doesn't have firestation.change_firedepartment permissions, so *should* have an empty PERMS qualifier
        c.login(**{'username': 'tester_mcgee', 'password': 'test'})
        response = c.get(reverse('firedepartment_detail', args=[fd.pk]))
        keys = cache._cache.keys()
        prefix = hash_for_cache(':True', '/departments/86610')
        self.assertTrue(any([prefix in x for x in keys]))

        # ensure that NONE of the keys blow out the max memcached key length
        self.assertFalse(any([len(k) > 250 for k in keys]))

    def test_homepage_auth_caching(self):
        cache = caches['default']
        cache.clear()

        c = Client()

        # Hit w/o being logged in
        resp = c.get(reverse('firestation_home'))
        prefix = hash_for_cache(':False', '/')
        keys = cache._cache.keys()
        self.assertTrue(any([prefix in x for x in keys]))

        # After logging in, we should have a different cache key for this page since we've authed
        c.login(**{'username': 'admin', 'password': 'admin'})
        resp2 = c.get(reverse('firestation_home'))
        prefix = hash_for_cache(':True', '/')
        keys = cache._cache.keys()
        self.assertTrue(any([prefix in x for x in keys]))

        # If the body of the response is the same, then we have issues
        self.assertNotEqual(resp.content, resp2.content)

    def test_robots(self):
        """
        Ensure robots.txt resolves.
        """
        c = Client()
        response = c.get(reverse('robots.txt'))
        self.assertEqual(response.status_code, 200)

    def test_media(self):
        """
        Ensure media page resolves.
        """
        c = Client()
        response = c.get(reverse('media'))
        self.assertEqual(response.status_code, 200)

    def test_station_number_from_name(self):
        """
        Tests the station number from name method on the FireStation model.
        """

        fs = self.create_firestation()
        fs.name = 'Engine 25'
        self.assertEqual(fs.station_number_from_name(), '25')

        fs.name = 'Lake Cities Fire Department Station 1'
        self.assertEqual(fs.station_number_from_name(), '1')

        fs.name = 'Lake Cities Fire Department Station 101'
        self.assertEqual(fs.station_number_from_name(), '101')

        fs.name = 'Central Oregon Coast Fire and Rescue District 7 Station 7400'
        self.assertEqual(fs.station_number_from_name(), '7400')

        fs.name = 'Walton County Fire Rescue Station 11A Mossy Head Fire and Rescue'
        self.assertEqual(fs.station_number_from_name(), '11')

        fs.name = 'Grand Traverse Rural Fire Department Battalion 3 Whitewater Township'
        self.assertEqual(fs.station_number_from_name(), None)

        fs.name = 'Fremont County Fire Protection District Battalion 12 Fort Washakie Fire Department'
        self.assertEqual(fs.station_number_from_name(), None)

    def test_create_station(self):
        """
        Tests the create station convenience method on the FireStation class.
        """
        fd = FireDepartment.objects.create(name='Test db', population=0)

        fs = FireStation.create_station(department=fd,
                                        address_string='9405 Devlins Grove Pl, Bristow, VA 20136',
                                        name='Fire Station 25')

        self.assertEqual(fs.station_number, 25)
        self.assertEqual(fs.name, 'Fire Station 25')
        self.assertEqual(fs.state, 'VA')
        self.assertIsNotNone(fs.station_address)
        self.assertEqual(fs.address, fs.station_address.address_line1)
        self.assertEqual(fs.city, fs.station_address.city)
        self.assertEqual(fs.zipcode, fs.station_address.postal_code)
        self.assertEqual(fs.geom, fs.station_address.geom)
        self.assertTrue(fs.department, fd)

    def test_api_formats(self):
        """
        Test that an API endpoint defaults to JSON vs XML and supports JSON and XML serialization formats
        """

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        for route in ['fire-departments', 'staffing', 'firestations']:
            # Test to ensure that the default route returns JSON vs XML
            resp = c.get(reverse('api_dispatch_list', args=[self.current_api_version, route]))
            self.assertEqual(resp.get('Content-type'), 'application/json')

            # Ensure that the existing ?format=json still returns JSON
            resp = c.get('{0}?format=json'.format(reverse('api_dispatch_list', args=[self.current_api_version, route]),))
            self.assertEqual(resp.get('Content-type'), 'application/json')

            # Make sure that returning XML is supported
            resp = c.get('{0}?format=xml'.format(reverse('api_dispatch_list', args=[self.current_api_version, route]),))
            self.assertTrue(resp.get('Content-type').startswith('application/xml'))

    def create_la_data(self):
        field_mappings = {
            'name': 'name',
            'department': 'department',
            'station_nu': 'station_number',
            'address_l1': 'station_address__address_line1',
            'address_l2': 'station_address__address_line2',
            'country': 'station_address__country',
            'state': 'station_address__state_province',
            'city': 'station_address__city',
            'zipcode': 'station_address__postal_code',
            'id': 'id',
        }

        FireDepartment.objects.create(id=87255, name='Los Angeles County Fire Department')

        feats = {
        "type": "FeatureCollection",
        "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },

        "features": [
        { "type": "Feature", "properties": { "id": 49620, "name": "Los Angeles County Fire Department Station 80", "department": 87255, "station_nu": 80, "address_l1": "1533 West Sierra Highway", "address_l2": None, "city": "Acton", "state": "CA", "zipcode": "93510-1894", "country": "US", "engine": 4, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.142042439999898, 34.487823576000039 ] } },
        { "type": "Feature", "properties": { "id": 16616, "name": "Los Angeles County Fire Department Station 65", "department": 87255, "station_nu": 65, "address_l1": "4206 North Cornell Road", "address_l2": None, "city": "Agoura", "state": "CA", "zipcode": "91301-2528", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.753559992999897, 34.134420014000057 ] } },
        { "type": "Feature", "properties": { "id": 795, "name": "Los Angeles County Fire Department Station 89", "department": 87255, "station_nu": 89, "address_l1": "29575 Canwood Street", "address_l2": None, "city": "Agoura Hills", "state": "CA", "zipcode": "91301-1558", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 2, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.769329790999905, 34.147909454000057 ] } },
        { "type": "Feature", "properties": { "id": 1334, "name": "Los Angeles County Fire Department Station 11", "department": 87255, "station_nu": 11, "address_l1": "2521 North El Molino Avenue", "address_l2": None, "city": "Altadena", "state": "CA", "zipcode": "91001-2317", "country": "US", "engine": 4, "engine_1": 5, "truck":None, "quint": 4, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.132906841999898, 34.188535251000076 ] } },
        { "type": "Feature", "properties": { "id": 26322, "name": "Los Angeles County Fire Department Station 12", "department": 87255, "station_nu": 12, "address_l1": "2760 North Lincoln Avenue", "address_l2": None, "city": "Altadena", "state": "CA", "zipcode": "91001-4961", "country": "US", "engine": 4, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point","coordinates": [ -118.158457743999918, 34.192918916000053 ] } },
        { "type": "Feature", "properties": { "id": 35013, "name": "Los Angeles County Fire Department Station 55", "department": 87255, "station_nu": 55, "address_l1": "945 Avalon Canyon Road", "address_l2": None, "city": "Avalon", "state": "CA", "zipcode": "90704", "country": "US", "engine": 1, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 1, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.33542908499993, 33.333073288000037 ] } },
        { "type": "Feature", "properties": { "id": 29712, "name": "Los Angeles County Fire Department Station 32", "department": 87255, "station_nu": 32, "address_l1": "605 North Angeleno Avenue", "address_l2": None, "city": "Azusa", "state": "CA", "zipcode": "91702-2904", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 3, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -117.910420849999923, 34.131861813000057 ] } }
        ]}

        staffing_fields = dict(Staffing.APPARATUS_SHAPEFILE_CHOICES)
        staffing_fields_aliases = dict((v, k) for k, v in staffing_fields.iteritems())

        for feature in feats['features']:
            mapping = {}
            address_fields = {}
            found_staffing_fields = []

            mapping['geom'] = Point(*feature['geometry']['coordinates'])
            address_geom = {'geom': Point(*feature['geometry']['coordinates'])}

            for field, value in feature['properties'].items():
                break_out = False

                # pass if this field is related to the staffing model
                for staffing_field_alias in staffing_fields.values():

                    if field.startswith(staffing_field_alias):
                        found_staffing_fields.append((field, value))
                        break_out = True

                if break_out:
                    continue

                firecares_field = field_mappings[field]

                if firecares_field == 'department':
                    value = FireDepartment.objects.get(id=value)

                if '__' in firecares_field:
                    address_fields[firecares_field.replace('station_address__', '')] = value

                else:
                    mapping[firecares_field] = value

            if address_fields:
                if address_fields['country']:
                    country, created = Country.objects.get_or_create(name=address_fields['country'])
                    address_fields['country'] = country

                    address, created = Address.objects.update_or_create(defaults=address_geom, **address_fields)
                    mapping['station_address'] = address
                    mapping['city'] = address.city
                    mapping['address'] = address.address_line1
                    mapping['state'] = address.state_province
                    mapping['zipcode'] = address.postal_code

            station = FireStation.objects.create(**mapping)

            for staffing_field, value in found_staffing_fields:

                if not value:
                    continue

                # if this a second apparatus (ie: engine_1, strip the suffix to correctly populate the apparatus type
                if staffing_field[-1].isdigit():
                    staffing_field = staffing_field.rsplit('_', 1)[0]

                Staffing.objects.create(apparatus=staffing_fields_aliases[staffing_field],
                                        personnel=value, firestation=station)

        call_command('createinitialrevisions', 'firestation')

    def test_data_import(self):

        c = Client()
        self.create_la_data()

        feats = {
        "type": "FeatureCollection",
        "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },

        "features": [
        { "type": "Feature", "properties": { "id": 49620, "name": "Los Angeles County Fire Department Station 3", "department": 87255, "station_nu": 3, "address_l1": "1534 West Sierra Highway", "address_l2": None, "city": "Acton", "state": "CA", "zipcode": "93510-1894", "country": "US", "engine": 4, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.145, 34.489 ] } },
        { "type": "Feature", "properties": { "id": 16616, "name": "Los Angeles County Fire Department Station 65", "department": 87255, "station_nu": 65, "address_l1": "4206 North Cornell Road", "address_l2": None, "city": "Agoura", "state": "CA", "zipcode": "91301-2528", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.753559992999897, 34.134420014000057 ] } },
        { "type": "Feature", "properties": { "id": 795, "name": "Los Angeles County Fire Department Station 89", "department": 87255, "station_nu": 89, "address_l1": "29575 Canwood Street", "address_l2": "None", "city": "Agoura Hills", "state": "CA", "zipcode": "91301-1558", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 2, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.769329790999905, 34.147909454000057 ] } },
        { "type": "Feature", "properties": { "id": 1334, "name": "Los Angeles County Fire Department Station 11", "department": 87255, "station_nu": 11, "address_l1": "2521 North El Molino Avenue", "address_l2": None, "city": "Altadena", "state": "CA", "zipcode": "91001-2317", "country": "US", "engine": 4, "engine_1": 5, "truck":None, "quint": 4, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.132906841999898, 34.188535251000076 ] } },
        { "type": "Feature", "properties": { "id": 26322, "name": "Los Angeles County Fire Department Station 12", "department": 87255, "station_nu": 12, "address_l1": "2760 North Lincoln Avenue", "address_l2": None, "city": "Altadena", "state": "CA", "zipcode": "91001-4961", "country": "US", "engine": 4, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point","coordinates": [ -118.158457743999918, 34.192918916000053 ] } },
        { "type": "Feature", "properties": { "id": 35013, "name": "Los Angeles County Fire Department Station 55", "department": 87255, "station_nu": 55, "address_l1": "945 Avalon Canyon Road", "address_l2": None, "city": "Avalon", "state": "CA", "zipcode": "90704", "country": "US", "engine": 1, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 1, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.33542908499993, 33.333073288000037 ] } },
        { "type": "Feature", "properties": { "id": 29712, "name": "Los Angeles County Fire Department Station 32", "department": 87255, "station_nu": 32, "address_l1": "605 North Angeleno Avenue", "address_l2": None, "city": "Azusa", "state": "CA", "zipcode": "91702-2904", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 3, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -117.910420849999923, 34.131861813000057 ] } },
        { "type": "Feature", "properties": { "name": "Los Angeles County Fire Department Station 56", "department": 87255, "station_nu": 56.0, "address_l1": "123 New Rd Canyon Road", "address_l2": None, "city": "Los Angeles", "state": "CA", "zipcode": "90210", "country": "US"}, "geometry": { "type": "Point", "coordinates": [ -118.45, 33.32 ] } },

        ]
        }

        sfu = SimpleUploadedFile("file.json", json.dumps(feats), content_type="application/json")
        response = c.post(reverse('uploads-new-json'), data={'file': sfu})

        # ensure user must have perms
        self.assertEqual(response.status_code, 302)
        sfu.seek(0)

        c.login(**{'username': 'admin', 'password': 'admin'})
        response = c.post(reverse('uploads-new-json'), data={'file': sfu})
        self.assertEqual(response.status_code, 200)
        js = json.loads(response.content)
        self.assertEqual(js['state'], 'UPLOADED')

        payload = [{'index': 0}]
        response = c.post('/importer-api/data-layers/{0}/configure/'.format(js['id']), data=json.dumps(payload),
                          content_type='application/json')
        self.assertEqual(response.status_code, 200)
        case = FireStation.objects.get(id=49620)

        self.assertEqual(case.station_number, 3)
        self.assertEqual(case.name, 'Los Angeles County Fire Department Station 3')
        self.assertEqual(case.department.id, 87255)
        self.assertEqual(case.station_address.address_line1, '1534 West Sierra Highway')
        self.assertEqual(case.geom.x, -118.145)
        self.assertEqual(case.geom.y, 34.489)
        self.assertEqual(Address.objects.all().count(), len(feats['features']) + 2)

        new_station = FireStation.objects.get(station_address__city='Los Angeles')
        self.assertTrue(new_station.station_number, 56)
        self.assertTrue(new_station.department.id, 87255)
        self.assertEqual(reversion.get_for_object(new_station).count(), 1)
        self.assertEqual(Revision.objects.count(), len(feats['features']) + 2 + Staffing.objects.count())
        self.assertEqual(reversion.get_for_object(case).count(), 2)

        self.assertEqual(2, Staffing.objects.filter(firestation_id=1334, apparatus='Engine').count())
        self.assertEqual(3, Staffing.objects.get(firestation_id=16616, apparatus='Engine').personnel)
        self.assertEqual(1, Staffing.objects.get(firestation_id=35013, apparatus__contains='Rescue').personnel)

    def test_ensure_no_handlers(self):
        self.assertEqual(GeoDjangoImport.enabled_handlers, [])

    def test_download_shapefile(self):
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})
        us = Country.objects.create(iso_code='US', name='United States')
        add = Address.objects.create(address_line1='123 Test Drive', country=us)

        fd = FireDepartment.objects.create(name='Test db',
                                           population=0,
                                           population_class=1,
                                           department_type='test')

        fs = FireStation.objects.create(station_number=25, name='Test Station', geom=Point(35, -77),
                                        district=MultiPolygon(Point(35, -77).buffer(.1)), department=fd,
                                        station_address=add)

        Staffing.objects.create(firestation=fs, apparatus='Engine', personnel=4)
        Staffing.objects.create(firestation=fs, apparatus='Engine', personnel=3)
        Staffing.objects.create(firestation=fs, apparatus='Engine', personnel=2)
        Staffing.objects.create(firestation=fs, apparatus='Ladder/Truck/Aerial', personnel=6)
        Staffing.objects.create(firestation=fs, apparatus='Ambulance/ALS', personnel=2)

        response = c.get(reverse('department_stations_shapefile', args=[fd.id, fd.slug]))
        self.assertEqual(response.status_code, 200)

        self.assertTrue(os.path.exists(response.content))

        from django.contrib.gis.gdal import DataSource
        ds = DataSource(response.content)

        for layer in ds:
            self.assertEqual(layer.num_feat, 1)
            expected_fields = ['id', 'name', 'department', 'station_nu', 'address_l1',
                               'address_l2', 'city', 'state', 'zipcode', 'country', 'engine',
                               'engine_1', 'engine_2', 'truck', 'quint', 'als_am', 'bls_am', 'rescue', 'boat', 'hazmat',
                               'chief', 'other']

            self.assertListEqual(layer.fields, expected_fields)

            for feature in layer:
                self.assertEqual(feature['engine'].value, 4)
                self.assertEqual(feature['engine_1'].value, 3)
                self.assertEqual(feature['engine_2'].value, 2)
                self.assertEqual(feature['truck'].value, 6)
                self.assertEqual(feature['quint'].value, 0)
                self.assertEqual(feature['als_am'].value, 2)
                self.assertEqual(feature['bls_am'].value, 0)
                self.assertEqual(feature['rescue'].value, 0)
                self.assertEqual(feature['boat'].value, 0)
                self.assertEqual(feature['hazmat'].value, 0)
                self.assertEqual(feature['chief'].value, 0)
                self.assertEqual(feature['other'].value, 0)

        self.assertTrue(response.has_header('X-Accel-Redirect'))

        response = c.get(reverse('department_districts_shapefile', args=[fd.id, fd.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('X-Accel-Redirect'))

    def test_documents(self):
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})
        try:
            fd = FireDepartment.objects.get(id=0)
        except FireDepartment.DoesNotExist:
            fd = FireDepartment.objects.create(id=0,
                                               name='Test db',
                                               population=0,
                                               population_class=1,
                                               department_type='test')

        # Documents page
        response = c.get(reverse('documents', args=[fd.id]))
        self.assertEqual(response.status_code, 200)

        # Upload document
        filename = 'unit_test.txt'
        file_content = 'file upload success'
        text_file = SimpleUploadedFile(filename, file_content, content_type='text/plain')
        response = c.post(reverse('documents', args=[fd.id]), {'file': text_file})
        self.assertEqual(response.status_code, 302)

        # Ensure that the document is owned by the uploaded user
        self.assertEqual(Document.objects.all().first().uploaded_by, self.user)

        # Download document
        response = c.get(reverse('documents_file', args=[fd.id, filename]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('X-Accel-Redirect'))

        # Delete document
        response = c.post(reverse('documents_delete', args=[fd.id]), {'filename': filename})
        self.assertEqual(response.status_code, 200)

        c.logout()
        c.login(username=self.non_admin_user, password=self.non_admin_password)

        response = c.get(reverse('documents', args=[fd.id]))
        self.assertEqual(response.status_code, 200)

        response = c.post(reverse('documents', args=[fd.id]), {'file': text_file})
        self.assertEqual(response.status_code, 302)

        response = c.get(reverse('documents_file', args=[fd.id, filename]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('X-Accel-Redirect'))

        # Delete document
        response = c.post(reverse('documents_delete', args=[fd.id]), {'filename': filename})
        self.assertEqual(response.status_code, 302)
