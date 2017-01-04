import os
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client
from requests_mock import Mocker
from .base import BaseFirecaresTestcase

User = get_user_model()


@Mocker()
class HelixSingleSignOnTests(BaseFirecaresTestcase):
    def setUp(self):
        self.logout_url = settings.HELIX_LOGOUT_URL
        self.token_url = settings.HELIX_TOKEN_URL
        self.whoami_url = settings.HELIX_WHOAMI_URL

    def load_mock(self, filename):
        with open(os.path.join(os.path.dirname(__file__), 'mocks/helix', filename), 'r') as f:
            return f.read()

    def setup_mocks(self, mock):
        mock.post(self.token_url, text=self.load_mock('get_access_token.json'))
        mock.get(self.whoami_url, text=self.load_mock('whoami.json'))

    def test_sso_login(self, mock):
        """
        Ensure that the Helix SSO login procedure works (and correctly disposes of Helix sessions on FireCARES logout)
        """
        self.setup_mocks(mock)

        c = Client()

        resp = c.get(reverse('oauth_redirect'))
        self.assertTrue('oauth_state' in c.session)
        self.assertEqual(resp.status_code, 302)
        # User is redirected to the FireCARES Helix login portal and then, after authenticating, redirected back to FireCARES
        # w/ the auth code and state

        resp = c.get('/?code=1231231234&state=badstate')
        # Having an out-of-sync state w/ current user's session should return a 400
        self.assertTrue(resp.status_code, 400)

        # Ensure that a user has been created and that NO
        resp = c.get('/?code=1231231234&state={}'.format(c.session['oauth_state']))
        self.assertTrue(resp.status_code, 200)

        user = User.objects.filter(username='iafc-testermctesting').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.first_name, 'Tester')
        self.assertEqual(user.last_name, 'McTesting')
        self.assertEqual(user.email, 'tester-iafc@prominentedge.com')
        resp = c.get(reverse('logout'))

        # Make sure that the user is redirected to the Helix logout URL
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], self.logout_url)

        # Ensure that user is actually logged out in FireCARES
        self.assertFalse(c.session.items())
