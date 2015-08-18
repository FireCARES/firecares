from .models import RecentlyUpdatedMixin

from datetime import timedelta
from django.contrib.auth import get_user_model, authenticate
from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.utils import timezone

User = get_user_model()


class CoreTests(TestCase):

    def test_home_requires_login(self):
        """
        Ensures the home page requires login.
        Note: This is just until we improve the home page.
        """

        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('login' in response.url)

    def test_departments_requires_login(self):
        """
        Ensures the home page requires login.
        Note: This is just until we are out of closed beta.
        """

        c = Client()
        response = c.get('/departments')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('login' in response.url)

    def test_recently_updated(self):
        """
        Tests the Recently Updated Mixin.
        """

        rum = RecentlyUpdatedMixin()
        rum.modified = timezone.now() - timedelta(days=11)
        self.assertFalse(rum.recently_updated)

        rum.modified = timezone.now() - timedelta(days=10)
        self.assertTrue(rum.recently_updated)

    def test_add_user(self):
        """
        Tests the add_user command.
        """

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username='foo')

        call_command('add_user', username='foo', password='bar', email='foo@bar.com')

        user = authenticate(username='foo', password='bar')
        self.assertIsNotNone(user)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

        call_command('add_user', username='foo_admin', password='bar', email='foo@bar.com', is_superuser=True)
        user = authenticate(username='foo_admin', password='bar')
        self.assertIsNotNone(user)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

        call_command('add_user', username='foo_admin1', password='bar', email='foo@bar.com', is_staff=True,
                     is_active=False)
        user = authenticate(username='foo_admin1', password='bar')
        self.assertIsNotNone(user)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_active)

        # Make sure no error is thrown when creating a user that already exists
        call_command('add_user', username='foo_admin1', password='bar', email='foo@bar.com', is_staff=True,
                     is_active=False)

    def test_registration_views(self):
        """
        Tests the registration view.
        """

        c = Client()

        with self.settings(REGISTRATION_OPEN=True):
            response = c.get(reverse('registration_register'))
            self.assertTrue(response.status_code, 200)

            c.post(reverse('registration_register'), data={'username': 'test',
                                                           'password1': 'test',
                                                           'password2': 'test',
                                                           'email': 'test@example.com'
                                                           })

            self.assertTrue(len(mail.outbox), 1)
            user = User.objects.get(username='test')
            self.assertFalse(user.is_active)
            self.assertFalse(user.is_superuser)
            self.assertFalse(user.is_staff)
            self.assertFalse(user.registrationprofile.activation_key_expired())

            response = c.get(reverse('registration_activate', kwargs={'activation_key':
                                                                      user.registrationprofile.activation_key}))
            # A 302 here means the activation succeeded
            self.assertEqual(response.status_code, 302)

            user = User.objects.get(username='test')
            self.assertTrue(user.is_active)
            self.assertTrue(user.registrationprofile.activation_key_expired())
            self.assertFalse(user.is_superuser)
            self.assertFalse(user.is_staff)

            # Check a bad activation code
            response = c.get(reverse('registration_activate', kwargs={'activation_key': 'nowaysdfsdfs'}))

            # A 200 here means the activation failed
            self.assertEqual(response.status_code, 200)

        # Make sure the user is forwarded to the registration closed page when REGISTRATION_OPEN is False
        with self.settings(REGISTRATION_OPEN=False):
            response = c.get(reverse('registration_register'))
            self.assertTrue(response.status_code, 302)

            response = c.get(reverse('registration_register'), follow=True)
            self.assertTrue(response.status_code, 200)
            self.assertEqual(response.request['PATH_INFO'], '/accounts/register/closed/')
