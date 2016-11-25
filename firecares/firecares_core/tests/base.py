from urlparse import urlsplit, urlunsplit
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.urlresolvers import resolve
from django.test import TestCase
from firecares.firestation.models import FireStation

User = get_user_model()


class BaseFirecaresTestcase(TestCase):
    def setUp(self):
        super(BaseFirecaresTestcase, self).setUp()
        self.response_capability_enabled = True
        self.current_api_version = 'v1'
        self.fire_station = self.create_firestation()

        self.admin_user, self.admin_creds = self.create_test_user('admin', 'admin', is_superuser=True)
        self.non_admin_user, self.non_admin_creds = self.create_test_user('non_admin', 'non_admin')
        self.non_accepted_user, self.non_accepted_creds = self.create_test_user('non_accepted', 'non_accepted', has_accepted_terms=False)

    def assert_redirect_to_login(self, response):
        self.assert_redirect_to(response, 'login')

    def assert_redirect_to(self, response, route_name):
        self.assertEqual(response.status_code, 302)
        split = urlsplit(response.url)
        path = split.path if split.path.endswith('/') else split.path + '/'
        shimmed = urlsplit(urlunsplit((split.scheme, split.netloc, path, split.query, split.fragment)))
        self.assertEqual(resolve(shimmed.path).url_name, route_name)

    def create_test_user(self, username, password, has_accepted_terms=True, is_superuser=False):
        user, created = User.objects.get_or_create(username=username, is_superuser=is_superuser)
        user.userprofile.has_accepted_terms = has_accepted_terms
        user.userprofile.save()

        if created:
            user.set_password(password)
            user.save()

        return user, dict(username=username, password=password)

    def create_firestation(self, **kwargs):
        return FireStation.objects.create(station_number=25, name='Test Station', geom=Point(35, -77),
                                          **kwargs)
