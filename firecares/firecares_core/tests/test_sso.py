import os
from uuid import uuid4
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from requests_mock import Mocker
from .base import BaseFirecaresTestcase

User = get_user_model()


@Mocker()
class SSOTests(BaseFirecaresTestcase):
    def setUp(self):
        self.service_wsdl = settings.SSO_SERVICE_URL
        self.service_root = self.service_wsdl.split('?')[0]
        self.valid_session = True
        self.user_info_updated = False
        self.disposed = []

    def load_mock(self, filename):
        with open(os.path.join(os.path.dirname(__file__), 'mocks', filename), 'r') as f:
            return f.read()

    def session_callback(self, request, context):
        if self.valid_session:
            return self.load_mock('valid_session.xml')
        else:
            return self.load_mock('invalid_session.xml')

    def disposed_callback(self, request, context):
        self.disposed.append({request: request, context: context})
        return self.load_mock('dispose_session.xml')

    def user_info_callback(self, request, context):
        if self.user_info_updated:
            return self.load_mock('updated_user_info.xml')
        else:
            return self.load_mock('user_info.xml')

    def setup_mocks(self, mock):
        mock.get(self.service_wsdl, text=self.load_mock('wsdl.xml'))
        # Zeep uses SOAP 1.1 by default, so we can match based on the SOAPAction request header
        mock.post(self.service_root,
                  request_headers={'SOAPAction': '"http://ibc.sso/ValidateSession"'},
                  text=self.session_callback)
        mock.post(self.service_root,
                  request_headers={'SOAPAction': '"http://ibc.sso/FetchUserInfo"'},
                  text=self.user_info_callback)
        mock.post(self.service_root,
                  request_headers={'SOAPAction': '"http://ibc.sso/DisposeSessionByUserToken"'},
                  text=self.disposed_callback)

    def test_sso_login(self, mock):
        """
        Ensure that the IMIS SSO login procedure works (and correctly disposes of IMIS sessions on FireCARES logout)
        """
        self.setup_mocks(mock)

        c = Client()
        uuid = uuid4()

        # Mock up a UUID token - redirected back to site from iMIS
        self.valid_session = False
        resp = c.get('/?ibcToken={}'.format(uuid))
        # Invalid session token will redirect the user back to login page
        self.assert_redirect_to(resp, 'login')
        self.assertFalse('ibcToken' in c.session)

        self.valid_session = True
        resp = c.get('/?ibcToken={}'.format(uuid))
        self.assertTrue('ibcToken' in c.session)
        # A user should be created with username = ImisId
        user = User.objects.filter(username='0559211').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.first_name, 'Tester')
        self.assertEqual(user.last_name, 'McTest')
        self.assertEqual(user.email, 'tester@prominentedge.com')
        c.logout()
        self.assertEqual(len(self.disposed), 1)

    def test_user_information_updates(self, mock):
        """
        Test user information is being updated upon subsequent login
        """

        self.setup_mocks(mock)

        c = Client()
        uuid = uuid4()
        c.get('/?ibcToken={}'.format(uuid))
        user = User.objects.filter(username='0559211').first()
        self.assertEqual(user.email, 'tester@prominentedge.com')

        c.logout()
        self.user_info_updated = True
        c.get('/?ibcToken={}'.format(uuid))
        user.refresh_from_db()
        self.assertEqual(user.email, 'testing@prominentedge.com')
