import os
import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client
from requests_mock import Mocker
from .base import BaseFirecaresTestcase
from firecares.firecares_core.models import PredeterminedUser, RegistrationWhitelist
from firecares.firestation.models import FireDepartment

User = get_user_model()


@Mocker()
class HelixSingleSignOnTests(BaseFirecaresTestcase):
    def setUp(self):
        self.logout_url = settings.HELIX_LOGOUT_URL
        self.token_url = settings.HELIX_TOKEN_URL
        self.whoami_url = settings.HELIX_WHOAMI_URL
        self.functional_title_matcher = re.compile(settings.HELIX_FUNCTIONAL_TITLE_URL + '\d*')
        self.valid_membership = False
        self.is_a_chief = False

    def token_callback(self, request, context):
        if self.valid_membership:
            return self.load_mock('get_access_token.json')
        else:
            return self.load_mock('not_a_member_token.json')

    def functional_title_callback(self, request, context):
        if self.is_a_chief:
            return '"FIRE_CHIEF"'
        else:
            return '"OTHER"'

    def load_mock(self, filename):
        with open(os.path.join(os.path.dirname(__file__), 'mocks/helix', filename), 'r') as f:
            return f.read()

    def setup_mocks(self, mock):
        mock.post(self.token_url, text=self.token_callback)
        mock.get(self.whoami_url, text=self.load_mock('whoami.json'))
        mock.get(self.functional_title_matcher, text=self.functional_title_callback)

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

        self.valid_membership = True

        # Ensure that a user has been created
        resp = c.get(reverse('oauth_redirect'))
        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))
        # We're not a chief, so make sure that we're gated
        self.assert_redirect_to(resp, 'show_message')

    def test_fire_chief_registration(self, mock):
        """
        Helix logins that have a functional title as FIRE_CHIEF can choose their department.
        """
        self.setup_mocks(mock)

        fd = FireDepartment.objects.create(id=1111, name='Chief test')

        c = Client()
        self.valid_membership = True
        self.is_a_chief = True

        resp = c.get(reverse('oauth_redirect'))
        self.assertTrue('oauth_state' in c.session)
        self.assertEqual(resp.status_code, 302)

        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))
        self.assert_redirect_to(resp, 'registration_choose_department')

        user = User.objects.filter(username='iafc-1234567').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.first_name, 'Tester')
        self.assertEqual(user.last_name, 'McTesting')
        self.assertEqual(user.email, 'tester-iafc@prominentedge.com')
        self.assertEqual(user.userprofile.functional_title, 'FIRE_CHIEF')

        # Fire chief should sent to choose their department, need to simulate disclaimer acceptance
        user.userprofile.has_accepted_terms = True
        user.userprofile.save()
        resp = c.post(reverse('registration_choose_department'), data={'state': 'MO', 'department': fd.id})

        # The second login for the user should automatically send them to the homepage as they've already submitted an
        # association request
        c.logout()
        c.get(reverse('oauth_redirect'))
        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))
        self.assert_redirect_to(resp, 'firestation_home')

        resp = c.get(reverse('logout'))

        # Make sure that the user is redirected to the Helix logout URL
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], self.logout_url)

        # Ensure that user is actually logged out in FireCARES
        self.assertFalse(c.session.items())

    def test_predetermined_fire_chief_registration(self, mock):
        """
        Helix logins considered "PredeterminedUsers" should automatically get department admin permissions.
        """
        self.setup_mocks(mock)

        fd = FireDepartment.objects.create(id=1234, name='testy2', population=2, featured=True)
        PredeterminedUser.objects.create(email='tester-iafc@prominentedge.com', department=fd)

        c = Client()
        # We shouldn't have to care about being a valid chief or member has the predetermined user list overrides
        self.valid_membership = False
        self.is_a_chief = False

        resp = c.get(reverse('oauth_redirect'))
        self.assertTrue('oauth_state' in c.session)
        self.assertEqual(resp.status_code, 302)
        # User is redirected to the FireCARES Helix login portal and then, after authenticating, redirected back to FireCARES
        # w/ the auth code and state

        # Ensure that a user has been created and that the user is redirected to his/her associated department
        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))
        self.assertRedirects(resp, '/departments/{}'.format(fd.id), fetch_redirect_response=False)

        user = User.objects.filter(email='tester-iafc@prominentedge.com').first()
        # Department should be associated w/ user
        self.assertEqual(user.userprofile.department, fd)
        self.assertEqual(user.userprofile.functional_title, 'OTHER')
        self.assertTrue(fd.is_admin(user))
        self.assertTrue(fd.is_curator(user))

    def test_whitelisted_helix_logins(self, mock):
        """
        Ensure that whitelisted users are able to login to FireCARES via Helix in addition to the other authentication providers.
        """
        self.setup_mocks(mock)

        fd = FireDepartment.objects.create(id=1234, name='testy2', population=2, featured=True)
        RegistrationWhitelist.objects.create(email_or_domain='tester-iafc@prominentedge.com', department=fd)

        c = Client()
        self.valid_membership = False

        resp = c.get(reverse('oauth_redirect'))
        self.assertTrue('oauth_state' in c.session)
        self.assertEqual(resp.status_code, 302)
        # User is redirected to the FireCARES Helix login portal and then, after authenticating, redirected back to FireCARES
        # w/ the auth code and state

        # Ensure that a user has been created and that the user is redirected to his/her associated department
        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))
        self.assertRedirects(resp, '/departments/{}'.format(fd.id), fetch_redirect_response=False)

        user = User.objects.filter(email='tester-iafc@prominentedge.com').first()
        # Department should be associated w/ user
        self.assertEqual(user.userprofile.department, fd)
        self.assertEqual(user.userprofile.functional_title, 'OTHER')
        self.assertFalse(fd.is_admin(user))
        self.assertFalse(fd.is_curator(user))

        user.delete()
        c.logout()
        RegistrationWhitelist.objects.all().delete()

        # Ensure that whitelisted users that DIDN'T get whitelisted by a specific department are correctly redirected
        RegistrationWhitelist.objects.create(email_or_domain='tester-iafc@prominentedge.com')

        resp = c.get(reverse('oauth_redirect'))
        resp = c.get(reverse('oauth_callback') + '?code=1231231234&state={}'.format(c.session['oauth_state']))

        user = User.objects.filter(email='tester-iafc@prominentedge.com').first()
        self.assert_redirect_to(resp, 'firestation_home')
        self.assertFalse(fd.is_admin(user))
        self.assertFalse(fd.is_curator(user))
