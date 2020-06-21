import json
import mock
import os
import string
from django.db import connections
from django.test.client import Client
from django.conf import settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Point, Polygon, MultiPolygon
from django.contrib.auth import get_user_model
from StringIO import StringIO
from firecares.usgs.models import UnincorporatedPlace, MinorCivilDivision
from firecares.firecares_core.models import Address, Country
from firecares.firestation.forms import StaffingForm, AddStationForm
from firecares.firestation.models import (Document, FireDepartment, FireStation,
                                          Staffing, IntersectingDepartmentLog)
from firecares.firestation.managers import CalculationsQuerySet
from reversion.models import Revision
from reversion import revisions as reversion
from firecares.firecares_core.models import AccountRequest
from firecares.firecares_core.tests.base import BaseFirecaresTestcase
from firecares.importers import GeoDjangoImport
from firecares.tasks.quality_control import test_all_departments_urls
from invitations.models import Invitation

User = get_user_model()


class FireStationTests(BaseFirecaresTestcase):
    def test_fd_thumbnails(self):
        """
        Tests that thumbnails are automatically created for new departments.
        """
        fd = FireDepartment.objects.create(name="Thumbnail Test Department", state='VA', geom=MultiPolygon([Point(0, 0).buffer(.1)]))
        fd.save()
        self.assertTrue(os.path.exists("/home/firecares/department-thumbnails/us-va-thumbnail-test-department.jpg"))

        fd.name = "Thumbnail test department 2"
        fd.save()
        self.assertTrue(os.path.exists("/home/firecares/department-thumbnails/us-va-thumbnail-test-department-2.jpg"))

    def test_auto_region_setting(self):
        """
        Tests that regions are automatically set on new departments.
        """
        department1 = FireDepartment.objects.create(name='Virginia Test Department', state='VA')
        department1.save()
        self.assertEqual(department1.region, "South")

        department2 = FireDepartment.objects.create(name='California Test Department', state='CA')
        department2.save()
        self.assertEqual(department2.region, "West")

        department3 = FireDepartment.objects.create(name='New York Test Department', state='NY')
        department3.save()
        self.assertEqual(department3.region, "Northeast")

        department4 = FireDepartment.objects.create(name='Illinois Test Department', state='IL')
        department4.save()
        self.assertEqual(department4.region, "Midwest")

        # If a department doesn't have a state set, its region should be an empty string.
        department5 = FireDepartment.objects.create(name='Null State Test Department')
        department5.save()
        self.assertEqual(department5.region, "")

        # If a department is in a state that doesn't exist, its region should be an empty string.
        department6 = FireDepartment.objects.create(name='Incorrectly Entered State Test Department', state='XX')
        department6.save()
        self.assertEqual(department6.region, "")

    def test_firestation_website_links(self):
        FireDepartment.objects.create(name='Good', website='http://www.google.com')
        test_all_departments_urls()
        self.assertTrue(len(mail.outbox) == 0, "email not sent to admin with errors")
        FireDepartment.objects.create(name='Bad', website='www.mawebsith.com')
        test_all_departments_urls()
        self.assertTrue(len(mail.outbox) == 1, "email sent to admin with errors")

    def test_api_authentication(self):
        """
        Tests users have to be authenticated to GET resources.
        """

        c = Client()

        for resource in ['staffing', 'fire-departments']:
            url = reverse('api_dispatch_list', args=[self.current_api_version, resource])
            response = c.get(url)
            self.assertEqual(response.status_code, 401)

            c.login(**self.admin_creds)
            response = c.get(url)
            self.assertEqual(response.status_code, 200)
            c.logout()

        # We ARE able to pull fire stations w/o logging in
        response = c.get(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']))
        self.assertEqual(response.status_code, 200)

    def test_add_capability_to_station(self):
        """
        Tests adding a capability via the API.
        """

        url = reverse('api_dispatch_list', args=[self.current_api_version, 'staffing'])
        station_uri = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                                       self.fire_station.id)
        c = Client()
        c.login(**self.admin_creds)

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

        c.login(**self.non_admin_creds)

        response = c.post(url, data=json.dumps(capability), content_type='application/json')
        self.assertEqual(response.status_code, 401)

        c.logout()

        # Anonymous users unable to add capabilities
        response = c.post(url, data=json.dumps(capability), content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_update_capability(self):
        """
        Tests updating the capability through the API.
        """

        capability = Staffing.objects.create(firestation=self.fire_station, personnel=4, apparatus='Boat')

        url = '{0}{1}/'.format(reverse('api_dispatch_list',
                                       args=[self.current_api_version, 'staffing']), capability.id)

        c = Client()
        c.login(**self.admin_creds)

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

        url = '{0}{1}/'.format(reverse('api_dispatch_list',
                                       args=[self.current_api_version, 'staffing']), capability.id)

        c = Client()
        c.login(**self.admin_creds)

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

        url = reverse('api_dispatch_list', args=[self.current_api_version, 'staffing'])
        station_uri = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                                       self.fire_station.id)
        c = Client()
        c.login(**self.admin_creds)

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

        url = '{0}?firestation={1}'.format(reverse('api_dispatch_list',
                                           args=[self.current_api_version, 'staffing']),
                                           self.fire_station.id)
        c = Client()
        c.login(**self.admin_creds)
        response = c.get(url)
        self.assertEqual(response.status_code, 200)

    def test_deleting_a_fire_station(self):
        """
        Tests that DELETE firestation requests through the API return a 405 (not supported).
        """

        url = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                               self.fire_station.id)
        c = Client()
        c.login(**self.admin_creds)

        response = c.delete(url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(FireStation.objects.get(id=self.fire_station.id))

    def test_deleting_a_fire_department(self):
        """
        Tests that DELETE department requests through the API return a 405 (not supported).
        """

        fd = self.load_la_department()
        url = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'fire-departments']),
                               fd.id)
        c = Client()
        c.login(**self.admin_creds)

        response = c.delete(url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(FireDepartment.objects.get(id=fd.id))

    def test_creating_a_fire_department(self):
        """
        Tests that POST department requests through the API return a 405 (not supported).
        """

        fd = self.load_la_department()
        url = reverse('api_dispatch_list', args=[self.current_api_version, 'fire-departments'])

        c = Client()
        c.login(**self.admin_creds)

        response = c.post(url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(FireDepartment.objects.get(id=fd.id))

    def test_creating_a_fire_station(self):
        """
        Tests that POST fire station requests through the API return a 405 (not supported).
        """

        fd = self.load_la_department()
        url = reverse('api_dispatch_list', args=[self.current_api_version, 'firestations'])

        c = Client()
        c.login(**self.admin_creds)

        response = c.post(url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(FireDepartment.objects.get(id=fd.id))

    def test_update_station_from_api(self):
        fd = self.load_la_department()
        fs = fd.firestation_set.first()
        url = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                               fs.id)

        count = FireStation.objects.all().count()
        c = Client()
        c.login(**self.admin_creds)

        response = c.get(url)
        js = json.loads(response.content)
        self.assertEqual(js['archived'], False)

        js['archived'] = True
        response = c.put(url, data=json.dumps(js), content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(count, FireStation.objects.all().count())
        self.assertTrue(FireStation.objects.get(id=fs.id).archived)

        # test as non_admin
        c.login(**self.non_admin_creds)
        response = c.get(url)
        js = json.loads(response.content)

        js['archived'] = False
        response = c.put(url, data=json.dumps(js), content_type='application/json')
        self.assertEqual(response.status_code, 401)

        # Assign change_firedepartment permissions on another department to verify object-level auth
        fd2 = self.load_arlington_department()

        fd2.add_curator(self.non_admin_user)
        response = c.put(url, data=json.dumps(js), content_type='application/json')
        self.assertEqual(response.status_code, 401)

        fd.add_curator(self.non_admin_user)
        response = c.put(url, data=json.dumps(js), content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(FireStation.objects.get(id=fs.id).archived)

    def test_read_firestation(self):
        url = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                               self.fire_station.id)

        c = Client()

        # Anonymous user should be able to read from the FireStation API
        response = c.get(url)
        self.assertEqual(response.status_code, 200)

        c.login(**self.non_admin_creds)

        response = c.get(url)
        self.assertEqual(response.status_code, 200)

    def test_read_firedepartment(self):
        fd = self.load_la_department()
        url = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'fire-departments']),
                               fd.id)

        c = Client()

        # MUST be logged in to use FireDepartment API
        response = c.get(url)
        self.assertEqual(response.status_code, 401)

        c.login(**self.non_admin_creds)

        response = c.get(url)
        self.assertEqual(response.status_code, 200)

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

        dep = FireDepartment.objects.all().extra(select={'val': 'select fts_document from firestation_firedepartment a where a.id=firestation_firedepartment.id'})
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

        response = c.get(reverse('firedepartment_list'), {'q': 'Ca'})
        self.assertTrue(lafd in response.context['object_list'])
        self.assertFalse(rfd in response.context['object_list'])

        response = c.get(reverse('firedepartment_list'), {'q': '', 'state': 'CA'})
        self.assertTrue(lafd in response.context['object_list'])

        # Ensure that syntax query errors don't raise 500
        try:
            response = c.get(reverse('firedepartment_list'), {'q': 'dept:1 \'& 1'})
        except Exception as e:
            self.fail(e)

    def test_generate_thumbnail_url(self):
        """
        Tests the generate thumbnail url logic.
        """

        lafd = FireDepartment.objects.create(name='Los Angeles', population=0, population_class=9, state='CA')

        # with no geometry make sure the thumbnail is the place holder
        self.assertEqual(lafd.generate_thumbnail(), '/static/firestation/theme/assets/images/content/property-1.jpg')
        lafd_poly = Polygon.from_bbox((-118.42170426600454, 34.09700463377199, -118.40170426600453, 34.117004633771984))

        us = Country.objects.create(iso_code='US', name='United States')
        address = Address.objects.create(address_line1='Test', country=us, geom=Point(-118.42170426600454, 34.09700463377199))
        lafd.headquarters_address = address
        lafd.save()

        # ensure a fd with no geometry uses the headquarters address location
        self.assertEqual(lafd.generate_thumbnail(), 'https://api.mapbox.com/styles/v1/prominentedge-ipsdi/ckb8cvy2z083c1io0xsvgj01j/static/pin-l-embassy+0074D9(-118.421704266,34.0970046338)/-118.421704266,34.0970046338,8/500x300?access_token={0}'.format(settings.MAPBOX_ACCESS_TOKEN))
        # ensure a fd with a geometry uses the centroid of the geometry
        lafd.geom = MultiPolygon([lafd_poly])
        self.assertEqual(lafd.generate_thumbnail(), 'https://api.mapbox.com/styles/v1/prominentedge-ipsdi/ckb8cvy2z083c1io0xsvgj01j/static/pin-l-embassy+0074D9(-118.411704266,34.1070046338)/-118.411704266,34.1070046338,8/500x300?access_token={0}'.format(settings.MAPBOX_ACCESS_TOKEN))

        # ensure the marker is not in the url when marker=False
        self.assertEqual(lafd.generate_thumbnail(marker=False), 'https://api.mapbox.com/styles/v1/prominentedge-ipsdi/ckb8cvy2z083c1io0xsvgj01j/static/-118.411704266,34.1070046338,8/500x300?access_token={0}'.format(settings.MAPBOX_ACCESS_TOKEN))

    def test_department_list_view(self):
        """
        Tests the list view.
        """

        fd = FireDepartment.objects.create(name='Adak Volunteer Fire Department', population=None)
        c = Client()
        c.login(**self.admin_creds)

        # regression test default params do not filter out the object
        response = c.get('/departments?name=adak&state=&region=&fdid=&sortBy=&limit=')
        self.assertTrue(fd in response.context['object_list'])

        # regression test default params do not filter out the object
        response = c.get('/departments?favorites=false&weather=false&cfai=false&name=adak&population=0+%2C+8175133&dist_model_score=0+%2C+380&limit=')
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
        c.login(**self.admin_creds)

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

        call_command('loaddata', 'firecares/firestation/fixtures/test_government_unit_association.json', stdout=StringIO())

        fd = FireDepartment.objects.get(pk=86610)
        place = UnincorporatedPlace.objects.get(pk=9254)
        div = MinorCivilDivision.objects.get(pk=31575)

        c = Client()
        response = c.get(reverse('firedepartment_update_government_units', args=[fd.pk]))

        # Make sure that we're redirected to login since we're not yet authenticated
        self.assert_redirect_to_login(response)

        # Login and make sure that we get a 200 back from the govt unit association update page
        c.login(**self.admin_creds)
        response = c.get(reverse('firedepartment_update_government_units', args=[fd.pk]))
        self.assertEqual(response.status_code, 200)

        response = c.post(reverse('firedepartment_update_government_units', args=[fd.pk]), {'unincorporated_places': [place.pk]})
        self.assertRedirects(response, reverse('firedepartment_detail_slug', args=[fd.pk, fd.slug]), fetch_redirect_response=False)
        # Make sure that the UnincorporatedPlace is associated
        self.assertEqual(fd.government_unit.first().object, place)

        # Update the geom for the FD
        response = c.post(reverse('firedepartment_update_government_units', args=[fd.pk]), {'minor_civil_divisions': [div.pk], 'update_geom': [1]})

        # Should have the exact same geom as the MinorCivilDivision that we associated
        fd.refresh_from_db()
        self.assertEqual(fd.geom, div.geom)

        # Should have a new population based on the government unit that we associated
        self.assertEqual(div.population, fd.population)

        # Test for ability to create new geoms for FireDepartments that didn't previously have a geometry
        fd_null_geom = FireDepartment.objects.get(pk=96582)
        div2 = MinorCivilDivision.objects.get(pk=19336)

        response = c.get(reverse('firedepartment_update_government_units', args=[fd_null_geom.pk]))
        self.assertEqual(response.status_code, 200)
        response = c.post(reverse('firedepartment_update_government_units', args=[fd_null_geom.pk]), {'minor_civil_divisions': [div2.pk], 'update_geom': [1]})
        self.assertRedirects(response, reverse('firedepartment_detail_slug', args=[fd_null_geom.pk, fd_null_geom.slug]), fetch_redirect_response=False)

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

    @mock.patch('geopy.geocoders.base.urllib_urlopen')
    def test_create_station(self, urllib_urlopen):
        """
        Tests the create station convenience method on the FireStation class.
        """

        c = urllib_urlopen.return_value
        c.read.return_value = open(os.path.join(os.path.dirname(__file__), 'mock/geocode.json')).read()
        c.headers.getparam.return_value = 'utf-8'

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
        c.login(**self.admin_creds)

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
            "type": "FeatureCollection",  # noqa
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },  # noqa

            "features": [
                { "type": "Feature", "properties": { "id": 49620, "name": "Los Angeles County Fire Department Station 80", "department": 87255, "station_nu": 80, "address_l1": "1533 West Sierra Highway", "address_l2": None, "city": "Acton", "state": "CA", "zipcode": "93510-1894", "country": "US", "engine": 4, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.142042439999898, 34.487823576000039 ] } },  # noqa
                { "type": "Feature", "properties": { "id": 16616, "name": "Los Angeles County Fire Department Station 65", "department": 87255, "station_nu": 65, "address_l1": "4206 North Cornell Road", "address_l2": None, "city": "Agoura", "state": "CA", "zipcode": "91301-2528", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.753559992999897, 34.134420014000057 ] } },  # noqa
                { "type": "Feature", "properties": { "id": 795, "name": "Los Angeles County Fire Department Station 89", "department": 87255, "station_nu": 89, "address_l1": "29575 Canwood Street", "address_l2": None, "city": "Agoura Hills", "state": "CA", "zipcode": "91301-1558", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 2, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.769329790999905, 34.147909454000057 ] } },  # noqa
                { "type": "Feature", "properties": { "id": 1334, "name": "Los Angeles County Fire Department Station 11", "department": 87255, "station_nu": 11, "address_l1": "2521 North El Molino Avenue", "address_l2": None, "city": "Altadena", "state": "CA", "zipcode": "91001-2317", "country": "US", "engine": 4, "engine_1": 5, "truck":None, "quint": 4, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.132906841999898, 34.188535251000076 ] } },  # noqa
                { "type": "Feature", "properties": { "id": 26322, "name": "Los Angeles County Fire Department Station 12", "department": 87255, "station_nu": 12, "address_l1": "2760 North Lincoln Avenue", "address_l2": None, "city": "Altadena", "state": "CA", "zipcode": "91001-4961", "country": "US", "engine": 4, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point","coordinates": [ -118.158457743999918, 34.192918916000053 ] } },  # noqa
                { "type": "Feature", "properties": { "id": 35013, "name": "Los Angeles County Fire Department Station 55", "department": 87255, "station_nu": 55, "address_l1": "945 Avalon Canyon Road", "address_l2": None, "city": "Avalon", "state": "CA", "zipcode": "90704", "country": "US", "engine": 1, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 1, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.33542908499993, 33.333073288000037 ] } },  # noqa
                { "type": "Feature", "properties": { "id": 29712, "name": "Los Angeles County Fire Department Station 32", "department": 87255, "station_nu": 32, "address_l1": "605 North Angeleno Avenue", "address_l2": None, "city": "Azusa", "state": "CA", "zipcode": "91702-2904", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 3, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -117.910420849999923, 34.131861813000057 ] } }  # noqa
            ]
        }

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
                    country, created = Country.objects.get_or_create(iso_code=address_fields['country'])
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
            "type": "FeatureCollection",  # noqa
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },  # noqa

            "features": [
                { "type": "Feature", "properties": { "station_id": 49620, "name": "Los Angeles County Fire Department Station 3", "department": 87255, "station_nu": 3, "address_l1": "1534 West Sierra Highway", "address_l2": None, "city": "Acton", "state": "CA", "zipcode": "93510-1894", "country": "US", "engine": 4, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.145, 34.489 ] } },  # noqa
                { "type": "Feature", "properties": { "station_id": 16616, "name": "Los Angeles County Fire Department Station 65", "department": 87255, "station_nu": 65, "address_l1": "4206 North Cornell Road", "address_l2": None, "city": "Agoura", "state": "CA", "zipcode": "91301-2528", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.753559992999897, 34.134420014000057 ] } },  # noqa
                { "type": "Feature", "properties": { "station_id": 795, "name": "Los Angeles County Fire Department Station 89", "department": 87255, "station_nu": 89, "address_l1": "29575 Canwood Street", "address_l2": "None", "city": "Agoura Hills", "state": "CA", "zipcode": "91301-1558", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 2, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.769329790999905, 34.147909454000057 ] } },  # noqa
                { "type": "Feature", "properties": { "station_id": 1334, "name": "Los Angeles County Fire Department Station 11", "department": 87255, "station_nu": 11, "address_l1": "2521 North El Molino Avenue", "address_l2": None, "city": "Altadena", "state": "CA", "zipcode": "91001-2317", "country": "US", "engine": 4, "engine_1": 5, "truck":None, "quint": 4, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.132906841999898, 34.188535251000076 ] } },  # noqa
                { "type": "Feature", "properties": { "station_id": 26322, "name": "Los Angeles County Fire Department Station 12", "department": 87255, "station_nu": 12, "address_l1": "2760 North Lincoln Avenue", "address_l2": None, "city": "Altadena", "state": "CA", "zipcode": "91001-4961", "country": "US", "engine": 4, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": None, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point","coordinates": [ -118.158457743999918, 34.192918916000053 ] } },  # noqa
                { "type": "Feature", "properties": { "station_id": 35013, "name": "Los Angeles County Fire Department Station 55", "department": 87255, "station_nu": 55, "address_l1": "945 Avalon Canyon Road", "address_l2": None, "city": "Avalon", "state": "CA", "zipcode": "90704", "country": "US", "engine": 1, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 1, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -118.33542908499993, 33.333073288000037 ] } },  # noqa
                { "type": "Feature", "properties": { "station_id": 29712, "name": "Los Angeles County Fire Department Station 32", "department": 87255, "station_nu": 32, "address_l1": "605 North Angeleno Avenue", "address_l2": None, "city": "Azusa", "state": "CA", "zipcode": "91702-2904", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 3, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -117.910420849999923, 34.131861813000057 ] } },  # noqa
                { "type": "Feature", "properties": { "name": "Los Angeles County Fire Department Station 56", "department": 87255, "station_nu": 56.0, "address_l1": "123 New Rd Canyon Road", "address_l2": None, "city": "Los Angeles", "state": "CA", "zipcode": "90210", "country": "US"}, "geometry": { "type": "Point", "coordinates": [ -118.45, 33.32 ] } },  # noqa
                { "type": "Feature", "properties": { "name": "Los Angeles County Fire Department Station 32", "department": 87255, "station_nu": 32, "address_l1": "605 North Angeleno Avenue", "address_l2": None, "city": "Azusa", "state": "CA", "zipcode": "91702-2904", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 3, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -117.910420849999923, 34.131861813000057 ] } },  # noqa
                { "type": "Feature", "properties": { "station_id": 29712, "name": "Los Angeles County Fire Department Station 32", "department": 87255, "station_nu": 32, "address_l1": "605 North Angeleno Avenue", "address_l2": None, "city": "Azusa", "state": "CA", "zipcode": "91702", "country": "US", "engine": 3, "engine_1": None, "truck": None, "quint": None, "als_am": None, "bls_am": None, "rescue": 3, "boat": None, "hazmat": None, "chief": None, "other": None }, "geometry": { "type": "Point", "coordinates": [ -117.910420849999923, 34.131861813000057 ] } },  # noqa
            ]
        }

        sfu = SimpleUploadedFile("file.json", json.dumps(feats), content_type="application/json")
        response = c.post(reverse('uploads-new-json'), data={'file': sfu})

        # ensure user must have perms
        self.assertEqual(response.status_code, 302)
        sfu.seek(0)

        c.login(**self.admin_creds)
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
        # We have 2 new stations, BUT station 32 is referred to twice in the dump (once w/o station_id)
        # so we will have 2 stations with nunmber = 32 in this case
        self.assertEqual(Address.objects.all().count(), len(feats['features']) + 1)

        self.assertEqual(FireStation.objects.count(), 10)
        self.assertEqual(Revision.objects.count(), len(feats['features']) - 2 + Staffing.objects.count())
        self.assertEqual(reversion.get_for_object(case).count(), 2)

        new_station = FireStation.objects.get(station_address__city='Los Angeles')
        self.assertTrue(new_station.station_number, 56)
        self.assertTrue(new_station.department.id, 87255)
        self.assertEqual(reversion.get_for_object(new_station).count(), 1)

        self.assertEqual(2, Staffing.objects.filter(firestation_id=1334, apparatus='Engine').count())
        self.assertEqual(3, Staffing.objects.get(firestation_id=16616, apparatus='Engine').personnel)
        self.assertEqual(1, Staffing.objects.get(firestation_id=35013, apparatus__contains='Rescue').personnel)

    def test_ensure_no_handlers(self):
        self.assertEqual(GeoDjangoImport.enabled_handlers, [])

    def test_download_shapefile(self):
        c = Client()
        c.login(**self.admin_creds)
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
            expected_fields = ['id', 'station_id', 'name', 'department', 'station_nu', 'address_l1',
                               'address_l2', 'city', 'state', 'zipcode', 'country', 'engine',
                               'engine_1', 'engine_2', 'truck', 'quint', 'als_am', 'bls_am', 'rescue', 'boat',
                               'hazmat', 'chief', 'other']

            self.assertListEqual(layer.fields, expected_fields)

            for feature in layer:
                self.assertEqual(feature['station_id'].value, fs.id)
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

        response = c.get(reverse('department_boundary_shapefile', args=[fd.id, fd.slug]))
        self.assertEqual(response.status_code, 200)

        response = c.get(reverse('firestation_boundary_shapefile', args=[fs.id, fs.slug]))
        self.assertEqual(response.status_code, 200)

    def test_documents(self):
        c = Client()
        c.login(**self.non_admin_creds)
        fd, _ = FireDepartment.objects.get_or_create(id=0,
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
        # Gated to only department data curators
        self.assertEqual(response.status_code, 401)

        fd.add_curator(self.non_admin_user)
        text_file = SimpleUploadedFile(filename, file_content, content_type='text/plain')
        response = c.post(reverse('documents', args=[fd.id]), {'file': text_file})
        # Redirect == success
        self.assert_redirect_to(response, 'documents_file')
        fd.remove_curator(self.non_admin_user)

        # Ensure that the document is owned by the uploaded user
        self.assertEqual(Document.objects.all().first().uploaded_by, self.non_admin_user)

        # Download document
        response = c.get(reverse('documents_file', args=[fd.id, filename]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('X-Accel-Redirect'))

        # Delete document, only available to curators
        response = c.post(reverse('documents_delete', args=[fd.id]), {'filename': filename})
        # Redirection to login == perm failure
        self.assert_redirect_to_login(response)

        fd.add_curator(self.non_admin_user)
        response = c.post(reverse('documents_delete', args=[fd.id]), {'filename': filename})
        self.assertEqual(response.status_code, 200)
        fd.remove_curator(self.non_admin_user)

        c.logout()
        c.login(**self.non_admin_creds)

        response = c.get(reverse('documents', args=[fd.id]))
        self.assertEqual(response.status_code, 200)

        response = c.post(reverse('documents', args=[fd.id]), {'file': text_file})
        self.assertEqual(response.status_code, 401)

        response = c.get(reverse('documents_file', args=[fd.id, filename]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('X-Accel-Redirect'))

        # Delete document
        response = c.post(reverse('documents_delete', args=[fd.id]), {'filename': filename})
        self.assert_redirect_to_login(response)

    def test_remove_intersecting_depts(self):
        us = Country.objects.create(iso_code='US', name='United States')
        address = Address.objects.create(address_line1='Test', country=us, geom=Point(-118.42170426600454, 34.09700463377199))

        geom = MultiPolygon([Polygon([(-118.62170426600454, 33.897004633771985),
                                      (-118.22170426600454, 33.897004633771985),
                                      (-118.22170426600454, 34.29700463377199),
                                      (-118.62170426600454, 34.29700463377199),
                                      (-118.62170426600454, 33.897004633771985)])])

        geom2 = MultiPolygon([geom.buffer(.2).envelope])

        fd, _ = FireDepartment.objects.get_or_create(id=0,
                                                     name='Test db',
                                                     population=90000,
                                                     population_class=1,
                                                     department_type='test',
                                                     headquarters_address=address,
                                                     geom=geom)

        fd2, _ = FireDepartment.objects.get_or_create(id=1,
                                                      name='Test db',
                                                      population=100000,
                                                      population_class=1,
                                                      department_type='test',
                                                      headquarters_address=address,
                                                      geom=geom2)

        c = Client()
        c.login(**self.non_admin_creds)
        response = c.get(reverse('remove_intersecting_departments', args=[fd2.id]))
        self.assertEqual(response.status_code, 302)

        response = c.post(reverse('remove_intersecting_departments', args=[fd2.id]), data={'departments': [0]})
        self.assertEqual(response.status_code, 302)

        c.logout()
        c.login(**self.admin_creds)

        response = c.get(reverse('remove_intersecting_departments', args=[fd2.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(fd, response.context['intersecting_departments'])

        response = c.post(reverse('remove_intersecting_departments', args=[fd2.id]), data={'departments': '0'}, follow=True)
        self.assertEqual(response.status_code, 200)

        fd2 = FireDepartment.objects.get(id=1)

        self.assertEqual(fd2.population, 10000)
        self.assertEqual(fd2.geom.area, geom2.difference(fd.geom).area)

        response = c.get(reverse('remove_intersecting_departments', args=[fd2.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(fd, response.context['intersecting_departments'])

        log = IntersectingDepartmentLog.objects.first()
        self.assertEqual(log.parent, fd2)
        self.assertEqual(log.removed_department, fd)

    def test_update_firedepartment_boundaries(self):
        us = Country.objects.create(iso_code='US', name='United States')
        address = Address.objects.create(address_line1='Test', country=us, geom=Point(-118.42170426600454, 34.09700463377199))
        geom = MultiPolygon([Polygon([(-118.62170426600454, 33.897004633771985),
                                      (-118.22170426600454, 33.897004633771985),
                                      (-118.22170426600454, 34.29700463377199),
                                      (-118.62170426600454, 34.29700463377199),
                                      (-118.62170426600454, 33.897004633771985)])])
        fd, _ = FireDepartment.objects.get_or_create(id=0,
                                                     name='Test geom update',
                                                     population=90000,
                                                     population_class=1,
                                                     department_type='test',
                                                     headquarters_address=address,
                                                     geom=geom)
        new_geom = """
{
  "geom": {
    "coordinates": [
      [
        [
          [
            0, 0
          ],
          [
            1, 1
          ],
          [
            2, 0
          ],
          [
            1, -1
          ],
          [
            0, 0
          ]
        ]
      ]
    ],
    "type": "MultiPolygon"
  }
}
"""

        single_poly = """
{
  "geom": {
    "coordinates": [
        [
          [
            0, 0
          ],
          [
            1, 1
          ],
          [
            2, 0
          ],
          [
            1, -1
          ],
          [
            0, 0
          ]
        ]
    ],
    "type": "Polygon"
  }
}"""

        c = Client()
        c.login(**self.non_admin_creds)
        url = '{root}{fd}/'.format(root=reverse('api_dispatch_list', args=[self.current_api_version, 'fire-departments']),
                                   fd=fd.id)
        # Ensure that a non-admin user can't update the department geom
        response = c.put(url, data=new_geom, content_type='application/json')
        self.assertEqual(response.status_code, 401)

        fd.add_curator(self.non_admin_user)

        response = c.put(url, data=new_geom, content_type='application/json')
        self.assertEqual(response.status_code, 204)
        response = c.get(url)
        self.assertDictEqual(json.loads(response.content).get('geom'), json.loads(new_geom).get('geom'))

        c.login(**self.admin_creds)
        response = c.put(url, data=new_geom, content_type='application/json')
        self.assertEqual(response.status_code, 204)

        # Be sure to ALSO support Polygon geometries in addition to MultiPolygon
        response = c.put(url, data=single_poly, content_type='application/json')
        self.assertEqual(response.status_code, 204)
        response = c.get(url)
        # Geometry will be converted to MultiPolygon
        self.assertDictEqual(json.loads(response.content).get('geom'), json.loads(new_geom).get('geom'))

    def test_department_permissions(self):
        fd = FireDepartment.objects.create(name='Test')

        fd.add_curator(self.non_admin_user)

        self.assertTrue(fd.is_curator(self.admin_user))
        self.assertTrue(fd.is_admin(self.admin_user))
        self.assertTrue(fd.is_curator(self.non_admin_user))
        self.assertFalse(fd.is_admin(self.non_admin_user))

        self.assertEqual(fd.get_department_admins(), [])

        fd.add_admin(self.non_admin_user)
        self.assertTrue(fd.is_admin(self.non_admin_user))
        self.assertEqual(fd.get_department_admins(), [self.non_admin_user])

    def test_request_account_from_department(self):
        """
        Test request for account submissions from department detail pages
        """

        fd = FireDepartment.objects.create(id=321, name='TEST')
        FireDepartment.objects.create(id=123, name='TEST2')

        fd.add_admin(self.non_admin_user)

        c = Client()

        resp = c.get(reverse('firedepartment_detail', args=[fd.id]))
        self.assertContains(resp, 'Is this your department?')
        self.assertContains(resp, '/accounts/registration-check/?department=321')

        # Departments with NO admins will redirect user to message view to inform them that FireCARES isn't enabled on this department
        resp = c.get(reverse('registration_preregister') + '?department=123')
        self.assert_redirect_to(resp, 'show_message')
        resp = c.get(resp['Location'])
        self.assertContains(resp, 'needs to enable FireCARES on this department')

        resp = c.post(reverse('account_request'), data={'email': 'tester@mytest.com', 'department': fd.id})
        self.assert_redirect_to(resp, 'show_message')
        resp = c.get(resp['Location'])
        self.assertContains(resp, 'You have been sent an email with the details of access policy')

        # Email should be sent to this department's admins notifying them that an account request has been submitted...
        self.assertEqual(len(mail.outbox), 1)
        self.assert_email_appears_valid(mail.outbox[0])
        self.assertEqual(mail.outbox[0].recipients(), ['non_admin@example.com', 'contact@firecares.org'])

        # Only department admin and superusers can see this page
        resp = c.get(reverse('admin_department_account_requests', args=[fd.id]) + '?email=tester@mytest.com')
        self.assert_redirect_to_login(resp)

        admin_client = Client()
        admin_client.login(**self.non_admin_creds)

        resp = admin_client.get(reverse('admin_department_account_requests', args=[fd.id]))
        self.assertEqual(resp.status_code, 400)

        # Test denial
        denied = {'email': 'tester@mytest.com', 'approved': 'False', 'message': 'Need more information, contact me at 314.555.1234'}
        resp = admin_client.post(reverse('admin_department_account_requests', args=[fd.id]) + '?email=tester@mytest.com', data=denied)
        self.assert_redirect_to(resp, 'firedepartment_detail_slug')

        self.assertEqual(len(mail.outbox), 2)
        map(self.assert_email_appears_valid, mail.outbox)
        self.assertEqual(mail.outbox[1].recipients(), ['tester@mytest.com'])
        self.assertTrue('Need more information' in mail.outbox[1].body)

        ar = AccountRequest.objects.filter(email='tester@mytest.com').first()
        self.assertIsNotNone(ar)
        self.assertEqual(ar.denied_by, self.non_admin_user)
        self.assertIsNone(ar.approved_by)
        self.assertEqual(ar.department, fd)

        # Test approval
        resp = c.post(reverse('account_request'), data={'email': 'tester2@mytest.com', 'department': fd.id})
        approved = {'email': 'tester2@mytest.com', 'approved': 'True'}
        resp = admin_client.post(reverse('admin_department_account_requests', args=[fd.id]) + '?email=tester2@mytest.com', data=approved)
        self.assert_redirect_to(resp, 'firedepartment_detail_slug')

        # 1 email for the request to the department admin, 1 for the invite to the end user
        self.assertEqual(len(mail.outbox), 4)
        self.assert_email_appears_valid(mail.outbox[2])
        self.assert_email_appears_valid(mail.outbox[3])
        user_email = mail.outbox[3]
        self.assertEqual(user_email.recipients(), ['tester2@mytest.com'])
        self.assertTrue('accept the invite' in user_email.body)
        inv = Invitation.objects.filter(email='tester2@mytest.com').first()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.departmentinvitation.department, fd)
        self.assertEqual(inv.inviter, self.non_admin_user)
        ar = AccountRequest.objects.filter(email='tester2@mytest.com').first()
        self.assertIsNotNone(ar)
        self.assertEqual(ar.department, fd)
        self.assertEqual(ar.approved_by, self.non_admin_user)
        self.assertIsNone(ar.denied_by)

        resp = admin_client.get(reverse('admin_department_account_requests', args=[fd.id]) + '?email=tester2@mytest.com')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'This request has already been approved')

    def test_update_firestation_boundaries(self):
        us = Country.objects.create(iso_code='US', name='United States')
        add = Address.objects.create(address_line1='123 Test Drive', country=us)

        fd = FireDepartment.objects.create(name='Test db',
                                           population=0,
                                           population_class=1,
                                           department_type='test')

        fs = FireStation.objects.create(station_number=25, name='Test Station', geom=Point(35, -77),
                                        district=None, department=fd,
                                        station_address=add)

        new_geom = """
{
  "district": {
    "coordinates": [
      [
        [
          [
            0, 0
          ],
          [
            1, 1
          ],
          [
            2, 0
          ],
          [
            1, -1
          ],
          [
            0, 0
          ]
        ]
      ]
    ],
    "type": "MultiPolygon"
  },
  "geom": {
    "coordinates": [
      35.0,
      -77.0
    ],
    "type": "Point"
  }
}
"""

        c = Client()
        c.login(**self.non_admin_creds)
        url = '{root}{fs}/'.format(root=reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                                   fs=fs.id)

        # Ensure that a non-admin user can't update the firestation boundaries
        response = c.put(url, data=new_geom, content_type='application/json')
        self.assertEqual(response.status_code, 401)

        fd.add_curator(self.non_admin_user)

        response = c.put(url, data=new_geom, content_type='application/json')
        self.assertEqual(response.status_code, 204)
        response = c.get(url)
        self.assertDictEqual(json.loads(response.content).get('district'), json.loads(new_geom).get('district'))

        c.login(**self.admin_creds)
        response = c.put(url, data=new_geom, content_type='application/json')
        self.assertEqual(response.status_code, 204)

    def test_local_number_loading(self):
        for i in [95512, 95559, 95560, 97963]:
            FireDepartment.objects.create(id=i, name='TEST-{}'.format(i))

        try:
            call_command('load-local-numbers', 'firecares/firestation/tests/mock/local_numbers.csv', stdout=StringIO())
        except:
            self.fail('Loading local #s that have a missing FireCARES department reference should NOT throw an exception')

        self.assertEqual(FireDepartment.objects.get(id=95512).iaff, '2876,3817')
        self.assertEqual(FireDepartment.objects.get(id=95559).iaff, '726')
        self.assertEqual(FireDepartment.objects.get(id=95560).iaff, '726')
        self.assertEqual(FireDepartment.objects.get(id=97963).iaff, '452,4378')

    def test_station_pagination(self):
        fd = FireDepartment.objects.create(name='TEST')
        for i in range(40):
            FireStation.objects.create(station_number=25, name='Test Station {}'.format(i), geom=Point(35, -77),
                                       department=fd)

        c = Client()
        try:
            c.get(reverse('firedepartment_detail', args=[fd.id]), {'page': '2\'A=0'})
        except Exception as e:
            self.fail(e)

        resp = c.get(reverse('firedepartment_detail', args=[fd.id]), {'page': '2'})
        self.assertEqual(resp.context['firestations'].number, 2)
        self.assertEqual(resp.context['firestations'].paginator.num_pages, 4)
        resp = c.get(reverse('firedepartment_detail', args=[fd.id]), {'page': '0'})
        self.assertEqual(resp.context['firestations'].number, 4)

    def test_superuser_addstation_form(self):
        """
        Tests capability validation via a AddStationForm object.
        """
        fd = FireDepartment.objects.create(name='Test db', population=0)

        form = AddStationForm({
            'station_number': 123,
            'address': '9405 Devlins Grove Pl',
            'city': 'Bristow',
            'name': 'Fire Station 25',
            'state': 'VA',
            'zipcode': 20136
        }, department_pk=fd.id)
        self.assertTrue(form.is_valid())

        emptyform = AddStationForm({})
        self.assertEqual(emptyform.errors, {
            'name': ['name cannot be empty'],
        })
        self.assertFalse(emptyform.is_valid())

    def test_superuser_addstation_page(self):
        """
        Tests capability for superuser to see addstation page
        """
        c = Client()
        fd = FireDepartment.objects.create(name='Test db', population=0)
        url = reverse('addstation', args=[fd.id])

        resp = c.get(url)
        self.assert_redirect_to_login(resp)

        c.login(**self.admin_creds)
        resp = c.get(url)
        self.assertEqual(resp.status_code, 200)

        capability = dict(station_number=123,
                          address='9405 Devlins Grove Pl',
                          city='Bristow',
                          name='Fire Station 25',
                          state='VA',
                          zipcode=20136
                          )

        response = c.post(url, data=json.dumps(capability), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FireStation.objects.all().count(), 1)
        c.logout()

        # Anonymous users unable to add capabilities
        response = c.post(url, data=json.dumps(capability), content_type='application/json')
        self.assertEqual(response.status_code, 302)
