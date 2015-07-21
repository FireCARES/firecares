"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import json
from .forms import ResponseCapabilityForm
from .models import FireStation, ResponseCapability
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model

User = get_user_model()


class FireStationTests(TestCase):

    def setUp(self):
        self.current_api_version = 'v1'
        self.fire_station = self.create_firestation()

        self.username = 'admin'
        self.password = 'admin'
        self.user, created = User.objects.get_or_create(username=self.username, is_superuser=True)

        if created:
            self.user.set_password(self.password)
            self.user.save()

    def create_firestation(self, **kwargs):
        return FireStation.objects.create(fips='123', station_number=25, name='Test Station', geom=Point(35, -77),
                                          **kwargs)

    def test_authentication(self):
        """
        Tests users have to be authenticated to GET resources.
        """
        c = Client()

        for resource in ['capabilities', 'firestations']:
            url = '{0}?format=json'.format(reverse('api_dispatch_list', args=[self.current_api_version, resource]),)
            response = c.get(url)
            self.assertTrue(response.status_code, 401)

            c.login(**{'username': 'admin', 'password': 'admin'})
            response = c.get(url)
            self.assertTrue(response.status_code, 200)

    def test_add_capability_to_station(self):
        """
        Tests adding a capability via the API.
        """
        url = '{0}?format=json'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'capabilities']),)
        station_uri = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                                       self.fire_station.id)
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        capability = dict(id=2,  # shouldn't have to put the id here
                          firestation=station_uri,
                          firefighter=1,
                          firefighter_emt=1,
                          firefighter_paramedic=1,
                          ems_emt=1,
                          ems_paramedic=1,
                          officer=1,
                          officer_paramedic=1,
                          ems_supervisor=1,
                          chief_officer=1
                          )

        response = c.post(url, data=json.dumps(capability), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.fire_station.responsecapability_set.all().count(), 1)

        unit = self.fire_station.responsecapability_set.all()[0]
        self.assertEqual(unit.firefighter, 1)
        self.assertEqual(unit.firefighter_emt, 1)
        self.assertEqual(unit.firefighter_paramedic, 1)
        self.assertEqual(unit.ems_emt, 1)
        self.assertEqual(unit.ems_paramedic, 1)
        self.assertEqual(unit.officer, 1)
        self.assertEqual(unit.officer_paramedic, 1)
        self.assertEqual(unit.ems_supervisor, 1)
        self.assertEqual(unit.chief_officer, 1)

    def test_update_capability(self):
        """
        Tests updating the capability through the API.
        """
        capability = ResponseCapability.objects.create(firestation=self.fire_station, firefighter=1, firefighter_emt=1,
                          firefighter_paramedic=1, ems_emt=1, ems_paramedic=1, officer=1, officer_paramedic=1,
                          ems_supervisor=1, chief_officer=1)

        url = '{0}{1}/?format=json'.format(reverse('api_dispatch_list',
                                                   args=[self.current_api_version, 'capabilities']), capability.id)

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        params = dict(firefighter=2, firefighter_emt=2, firefighter_paramedic=2, ems_emt=2, ems_paramedic=2, officer=2,
                      officer_paramedic=2, ems_supervisor=2, chief_officer=2)

        response = c.put(url, data=json.dumps(params), content_type='application/json')
        self.assertEqual(response.status_code, 204)

        updated_capability = ResponseCapability.objects.get(id=capability.id)
        self.assertEqual(updated_capability.firefighter, 2)
        self.assertEqual(updated_capability.firefighter_emt, 2)
        self.assertEqual(updated_capability.firefighter_paramedic, 2)
        self.assertEqual(updated_capability.ems_emt, 2)
        self.assertEqual(updated_capability.ems_paramedic, 2)
        self.assertEqual(updated_capability.officer, 2)
        self.assertEqual(updated_capability.officer_paramedic, 2)
        self.assertEqual(updated_capability.ems_supervisor, 2)
        self.assertEqual(updated_capability.chief_officer, 2)

    def test_deleting_a_capability(self):
        """
        Tests deleting the capability through the API.
        """
        capability = ResponseCapability.objects.create(firestation=self.fire_station, firefighter=1, firefighter_emt=1,
                          firefighter_paramedic=1, ems_emt=1, ems_paramedic=1, officer=1, officer_paramedic=1,
                          ems_supervisor=1, chief_officer=1)

        url = '{0}{1}/?format=json'.format(reverse('api_dispatch_list',
                                                   args=[self.current_api_version, 'capabilities']), capability.id)

        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        response = c.delete(url)
        self.assertEqual(response.status_code, 204)

        # make sure it actually deleted the object.
        with self.assertRaises(ResponseCapability.DoesNotExist):
            ResponseCapability.objects.get(id=capability.id)

    def test_response_capability_form_validation(self):
        """
        Tests capability validation via a Form object.
        """

        capability = dict(firestation=self.fire_station.id,
                          firefighter='test',
                          firefighter_emt=True,
                          firefighter_paramedic=100,
                          ems_emt=False,
                          ems_paramedic=2312312312312323,
                          officer='testing',
                          officer_paramedic=-1,
                          ems_supervisor='e',
                          chief_officer=False,
                          apparatus='whatever'
                          )

        rc = ResponseCapabilityForm(capability)
        for key in capability.keys():
            if key not in ['firestation']:
                self.assertTrue(key in rc.errors, 'The invalid field:{0} was not returned in the error message.'
                                .format(key))

    def test_add_capability_validation(self):
        """
        Tests capability validation via the API.
        """
        url = '{0}?format=json'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'capabilities']),)
        station_uri = '{0}{1}/'.format(reverse('api_dispatch_list', args=[self.current_api_version, 'firestations']),
                                       self.fire_station.id)
        c = Client()
        c.login(**{'username': 'admin', 'password': 'admin'})

        capability = dict(id=2,  # shouldn't have to put the id here
                          firestation=station_uri,
                          firefighter='test',
                          firefighter_emt=True,
                          firefighter_paramedic=100,
                          ems_emt=False,
                          ems_paramedic=2312312312312323,
                          officer='testing',
                          officer_paramedic=-1,
                          ems_supervisor='e',
                          chief_officer=False,
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
                                                               args=[self.current_api_version, 'capabilities']),
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
