import os
from enum import Enum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client
from requests_mock import Mocker
from .base import BaseFirecaresTestcase
from firecares.firecares_core.models import PredeterminedUser
from firecares.firestation.models import FireDepartment

User = get_user_model()


class TokenState(Enum):
    invalid_membership = 1
    valid_membership = 2
    valid_fire_chief = 3
    valid_predetermined_fire_chief = 4


@Mocker()
class HelixSingleSignOnTests(BaseFirecaresTestcase):
    def setUp(self):
        self.logout_url = settings.HELIX_LOGOUT_URL
        self.token_url = settings.HELIX_TOKEN_URL
        self.whoami_url = settings.HELIX_WHOAMI_URL
        self.state = TokenState.invalid_membership

    def token_callback(self, request, context):
        if self.state == TokenState.valid_membership:
            return self.load_mock('get_access_token.json')
        elif self.state == TokenState.invalid_membership:
            return self.load_mock('not_a_member_token.json')
        elif self.state == TokenState.valid_fire_chief:
            # TODO
            pass
        elif self.state == TokenState.valid_predetermined_fire_chief:
            # TODO
            pass

    def load_mock(self, filename):
        with open(os.path.join(os.path.dirname(__file__), 'mocks/helix', filename), 'r') as f:
            return f.read()

    def setup_mocks(self, mock):
        mock.post(self.token_url, text=self.token_callback)
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

        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state=badstate')
        # Having an out-of-sync state w/ current user's session should return a 400
        self.assertTrue(resp.status_code, 400)

        # Ensure that only IAFC MEMBERS can login when using Helix
        resp = c.get(reverse('oauth_redirect'))
        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))
        self.assert_redirect_to(resp, 'show_message')

        self.state = TokenState.valid_membership

        # Ensure that a user has been created
        resp = c.get(reverse('oauth_redirect'))
        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))
        self.assertTrue(resp.status_code, 200)

        user = User.objects.filter(username='iafc-1234567').first()
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

    def test_fire_chief_registration(self, mock):
        """
        Helix logins that have a functional title as FIRE_CHIEF can choose their department.
        """
        self.setup_mocks(mock)
        pass

    def test_predetermined_fire_chief_registration(self, mock):
        """
        Helix logins considered "PredeterminedUsers" should automatically get department admin permissions.
        """
        self.setup_mocks(mock)

        fd = FireDepartment.objects.create(name='testy2', population=2, featured=True)
        PredeterminedUser.objects.create(email='tester-iafc@prominentedge.com', department=fd)

        c = Client()
        self.state = TokenState.valid_membership

        resp = c.get(reverse('oauth_redirect'))
        self.assertTrue('oauth_state' in c.session)
        self.assertEqual(resp.status_code, 302)
        # User is redirected to the FireCARES Helix login portal and then, after authenticating, redirected back to FireCARES
        # w/ the auth code and state

        # Ensure that a user has been created
        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))
        self.assertTrue(resp.status_code, 200)

        user = User.objects.filter(username='iafc-1234567').first()
        # Department should be associated w/ user
        self.assertEqual(user.userprofile.department, fd)
        self.assertTrue(fd.is_admin(user))
        self.assertFalse(fd.is_curator(user))
