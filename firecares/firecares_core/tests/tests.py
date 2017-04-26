import json
import re
from StringIO import StringIO
from urlparse import urlparse
from datetime import timedelta
from urlparse import urlsplit
from django.contrib.auth import get_user_model, authenticate
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse, resolve
from django.test import Client
from django.utils import timezone
from bs4 import BeautifulSoup
from firecares.firecares_core.models import RecentlyUpdatedMixin, AccountRequest, RegistrationWhitelist, PredeterminedUser, DepartmentAssociationRequest
from firecares.firestation.models import FireDepartment
from .base import BaseFirecaresTestcase

User = get_user_model()


class CoreTests(BaseFirecaresTestcase):
    fixtures = ['test_forgot.json']

    def setUp(self):
        if settings.OUTPUT_EMAILS_TO_FILES:
            settings.EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
            settings.EMAIL_FILE_PATH = '/tmp/testEmails'

    def test_sitemap(self):
        """
        Ensures the generated sitemap has correct priorities
        """

        FireDepartment.objects.create(name='testy2', population=2, featured=True)
        FireDepartment.objects.create(name='testy3', population=3)
        FireDepartment.objects.create(name='testy4', population=4)

        call_command('refresh_sitemap')

        c = Client()
        response = c.get('/sitemap.xml')

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'xml')
        sitemap_list = soup.find_all('loc')
        self.assertEqual(len(sitemap_list), 2)  # Should have 2 sitemap items

        departments = BeautifulSoup(open('/tmp/sitemaps/sitemap-departments-1.xml'))
        department_list = departments.find_all('url')

        self.assertEqual(len(department_list), 3)  # 3 test departments
        # find the three elements
        for testy in department_list:
            if 'testy2' in testy.loc.get_text():
                testy2 = testy
            elif 'testy3' in testy.loc.get_text():
                testy3 = testy
            elif 'testy4' in testy.loc.get_text():
                testy4 = testy
        # assert that testy2 has higher priority than testy4 (because its featured) and 4 has more than 3
        self.assertGreater(float(testy2.priority.get_text()), float(testy4.priority.get_text()))
        self.assertGreater(float(testy4.priority.get_text()), float(testy3.priority.get_text()))

    def test_home_does_not_require_login(self):
        """
        Ensures the home page requires login.
        Note: This is just until we improve the home page.
        """

        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)

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

        call_command('add_user', 'foo', 'bar', 'foo@bar.com')

        user = authenticate(username='foo', password='bar')
        self.assertIsNotNone(user)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

        call_command('add_user', 'foo_admin', 'bar', 'foo@bar.com', is_superuser=True)
        user = authenticate(username='foo_admin', password='bar')
        self.assertIsNotNone(user)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

        call_command('add_user', 'foo_admin1', 'bar', 'foo@bar.com', is_staff=True, is_active=False)
        user = authenticate(username='foo_admin1', password='bar')
        self.assertIsNotNone(user)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_active)

        # Make sure no error is thrown when creating a user that already exists
        call_command('add_user', 'foo_admin1', 'bar', 'foo@bar.com', is_staff=True, is_active=False)

    def test_registration_views(self):
        """
        Tests the registration view.
        """

        c = Client()

        with self.settings(REGISTRATION_OPEN=True):
            response = c.get(reverse('registration_register'))
            # Must validate email before going through registration
            self.assert_redirect_to(response, 'registration_preregister')

            # Whitelist this address for optimal path testing
            RegistrationWhitelist.objects.create(email_or_domain='test_registration@example.com')

            # Ensure that email addresses that are NOT whitelisted create an account request
            resp = c.post(reverse('account_request'), data={'email': 'badtest@example.com'})
            self.assert_redirect_to(resp, 'show_message')

            # For emails that are whitelisted, redirect to the registration form
            resp = c.post(reverse('account_request'), data={'email': 'test_registration@example.com'})
            self.assert_redirect_to(resp, 'registration_register')
            self.assertTrue('email_whitelisted' in c.session)
            # Email address is pulled from session versus form
            response = c.post(reverse('registration_register'), data={'username': 'test_registration',
                                                                      'first_name': 'fname',
                                                                      'last_name': 'lname',
                                                                      'password1': 'test',
                                                                      'password2': 'test'
                                                                      })

            user = User.objects.get(username='test_registration')
            self.assertFalse(user.is_active)
            self.assertFalse(user.is_superuser)
            self.assertFalse(user.is_staff)
            self.assertEqual(user.email, 'test_registration@example.com')
            self.assertFalse(user.registrationprofile.activation_key_expired())
            self.assertTrue(len(mail.outbox), 1)
            self.assert_email_appears_valid(mail.outbox[0])

            response = c.get(reverse('registration_activate', kwargs={'activation_key':
                                                                      user.registrationprofile.activation_key}))
            # A 302 here means the activation succeeded
            self.assertEqual(response.status_code, 302)

            user = User.objects.get(username='test_registration')
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

    def test_whitelisted_registration_with_account_request(self):
        """
        Ensure that whitelisted users with account requests are able to register.
        """
        c = Client()

        AccountRequest.objects.create(email='test@example.com')
        RegistrationWhitelist.objects.create(email_or_domain='test@example.com')

        resp = c.post(reverse('account_request'), data={'email': 'test@example.com'})
        self.assertTrue('email_whitelisted' in c.session)

        self.assert_redirect_to(resp, 'registration_register')

    def test_password_reset(self):
        """
        Tests the forgotten/reset password workflow.
        """

        c = Client()

        resp = c.get(reverse('password_reset'))
        self.assertTrue(resp.status_code, 200)

        resp = c.post(reverse('password_reset'), data={'email': 'test@example.com'})
        self.assertEqual(resp.status_code, 302)

        self.assertEqual(len(mail.outbox), 1)
        self.assert_email_appears_valid(mail.outbox[0])

        token = resp.context[0]['token']
        uid = resp.context[0]['uid']

        # Grab the token and uidb64 so that we can hit the reset url
        resp = c.get(reverse('password_reset_confirm', kwargs={'token': token, 'uidb64': uid}))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.template_name.endswith('password_reset_confirm.html'))

        resp = c.post(reverse('password_reset_confirm', kwargs={'token': token, 'uidb64': uid}),
                      {'new_password1': 'mynewpassword', 'new_password2': 'mynewpassword'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resolve(urlsplit(resp.url).path).url_name, 'password_reset_complete')

        resp = c.post(reverse('login'), {'username': 'tester_mcgee', 'password': 'mynewpassword'})

        # User is returned to the login page on error vs redirected by default
        self.assertEqual(resp.status_code, 302)
        self.assertNotEqual(resolve(urlsplit(resp.url).path).url_name, 'login')

    def test_forgot_username(self):
        """
        Tests the forgot username workflow.
        """

        c = Client()
        resp = c.get(reverse('forgot_username'))
        self.assertEqual(resp.status_code, 200)

        resp = c.post(reverse('forgot_username'), {'email': 'test@example.com'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resolve(urlsplit(resp.url).path).url_name, 'username_sent')

        self.assertEqual(len(mail.outbox), 1)
        self.assert_email_appears_valid(mail.outbox[0])
        # Make sure that the username is actually in the email (otherwise what's the point?)
        self.assertTrue('tester_mcgee' in mail.outbox[0].body)

    def test_change_password(self):
        """
        Test the change password worflow.
        """

        c = Client()
        resp = c.get(reverse('password_change'))
        # Should redirect to login view since password_change requires a logged-in user
        self.assert_redirect_to_login(resp)

        # Should redirect to the password_change page after login
        resp = c.post(reverse('login') + '?next=' + reverse('password_change'), {'username': 'tester_mcgee', 'password': 'test'})
        self.assert_redirect_to(resp, 'password_change')

        # Fill out the change password form w/ invalid old password_change
        resp = c.post(reverse('password_change'), {'old_password': 'badpassword'})
        # No redirect means something bad happened
        self.assertEqual(resp.status_code, 200)

        # Fill out the change password form w/ new passwords that don't match
        resp = c.post(reverse('password_change'),
                      {'old_password': 'test',
                       'new_password1': 'brandnewpassword',
                       'new_password2': 'uhohthiswontmatch'})
        self.assertEqual(resp.status_code, 200)

        # Fill out using valid params that would change password
        resp = c.post(reverse('password_change'),
                      {'old_password': 'test',
                       'new_password1': 'newerpassword',
                       'new_password2': 'newerpassword'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resolve(urlsplit(resp.url).path).url_name, 'password_change_done')

    def test_contact_us(self):
        """
        Test the contact us form submission
        """

        c = Client()
        with self.settings(ADMINS=(('Test Admin', 'admin@example.com'),)):
            # Disable captcha checking
            settings.RECAPTCHA_SECRET = ''
            resp = c.post(reverse('contact_us'), {
                          'name': 'Tester McGee',
                          'email': 'test@example.com',
                          'message': 'This is a test'})

            self.assertRedirects(resp, reverse('contact_thank_you'))
            self.assertEqual(len(mail.outbox), 1)
            self.assert_email_appears_valid(mail.outbox[0])
            self.assertItemsEqual(mail.outbox[0].reply_to, ['test@example.com'])

    def test_display_404_page(self):
        c = Client()
        resp = c.get('/notarealpage/')
        self.assertContains(resp, 'Page not found', status_code=404)

    def test_request_login(self):
        """
        Tests the account request workflow.
        """
        view = 'account_request'
        c = Client()

        with self.settings(ADMINS=(('Test Admin', 'admin@example.com'),)):
            resp = c.post(reverse(view), {'email': 'test_request_login@example.com'}, follow=True)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(1, AccountRequest.objects.count())

            # Ensure duplicates are handled gracefully.
            resp = c.post(reverse(view), {'email': 'test_request_login@example.com'}, follow=True)
            self.assertEqual(resp.status_code, 200)

            # Make sure admin email is triggered.
            self.assertEqual(len(mail.outbox), 1)
            self.assert_email_appears_valid(mail.outbox[0])

    def test_signup_when_account_exists(self):
        """
        Test that an account request for an email that already exists redirects to login.
        """
        with self.settings(ADMINS=(('Test Admin', 'admin@example.com'),)):
            c = Client()

            user, creds = self.create_test_user('signup_tester', 'password', email='tester@example.com')
            resp = c.post(reverse('account_request'), dict(email='tester@example.com'))
            self.assert_redirect_to_login(resp)

    def test_email_whitelisting(self):
        """
        Ensure that email addresses are correctly whitelisted.
        """

        fd = FireDepartment.objects.create(name='PredeterminedUserTest')
        RegistrationWhitelist.objects.create(email_or_domain='gmail.com')
        RegistrationWhitelist.objects.create(email_or_domain='test@example.com')
        PredeterminedUser.objects.create(email='predetermined_tester@myfd.org', department=fd)
        RegistrationWhitelist.objects.create(email_or_domain='department.gov', department=fd)
        RegistrationWhitelist.objects.create(email_or_domain='test@myfd.org', department=fd)

        self.assertTrue(RegistrationWhitelist.is_whitelisted('joe@gmail.com'))
        self.assertTrue(RegistrationWhitelist.is_whitelisted('test@example.com'))
        self.assertFalse(RegistrationWhitelist.is_whitelisted('badtest@example.com'))
        self.assertFalse(RegistrationWhitelist.is_whitelisted('testbad@example.com'))
        self.assertFalse(RegistrationWhitelist.is_whitelisted('test@example.com.uk'))
        self.assertFalse(RegistrationWhitelist.is_whitelisted('test@gmail.com.uk'))
        self.assertTrue(RegistrationWhitelist.is_whitelisted('predetermined_tester@myfd.org'))
        self.assertFalse(RegistrationWhitelist.is_whitelisted('anothertester@myfd.org'))
        self.assertTrue(RegistrationWhitelist.is_whitelisted('test@department.gov'))
        self.assertTrue(RegistrationWhitelist.is_department_whitelisted('test@department.gov'))
        self.assertTrue(RegistrationWhitelist.is_whitelisted('test@myfd.org'))
        self.assertFalse(RegistrationWhitelist.is_whitelisted('me@myfd.org'))
        self.assertFalse(RegistrationWhitelist.is_department_whitelisted('me@myfd.org'))
        self.assertTrue(RegistrationWhitelist.is_department_whitelisted('test@myfd.org'))
        self.assertEqual(RegistrationWhitelist.get_department_for_email('test@myfd.org'), fd)
        self.assertIsNone(RegistrationWhitelist.get_department_for_email('invalid@myfd.org'))

        # Whitelist check should be case insensitive
        self.assertTrue(RegistrationWhitelist.is_whitelisted('Joe@GMAIL.COM'))
        self.assertTrue(RegistrationWhitelist.is_whitelisted('Test@MYFD.org'))

    def test_invite_workflow(self):
        fd = self.load_la_department()
        fd2 = self.load_arlington_department()

        dept_user = Client()
        anon_user = Client()
        fd.add_admin(self.non_admin_user)
        dept_user.login(**self.non_admin_creds)

        # If the inviting user isn't an admin on the department that the invitation for, then 401
        resp = dept_user.post(reverse('invitations:send-json-invite'), data=json.dumps([dict(department_id=fd2.id, email='joe@test.com')]), content_type='application/json')
        self.assertEqual(resp.status_code, 401)

        resp = dept_user.post(reverse('invitations:send-json-invite'), data=json.dumps([dict(department_id=fd.id, email='joe@test.com')]), content_type='application/json')
        self.assertEqual(resp.status_code, 201)

        # Extract invite link from outbound email and start registration
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assert_email_appears_valid(mail.outbox[0])
        self.assertIn('non_admin@example.com', msg.body)
        self.assertIn('/invitations/accept-invite/', msg.body)
        url = re.findall('(https?://\S+)', msg.body)[0]
        path = urlparse(url).path
        resp = anon_user.get(path)
        self.assert_redirect_to(resp, 'registration_register')

        # Fill out registration form and activate account
        form = dict(username='inviteuser', first_name='Invite', last_name='User', password1='secret1', password2='secret1')
        resp = anon_user.post(reverse('registration_register'), data=form)
        self.assert_redirect_to(resp, 'registration_complete')
        self.assertEqual(len(mail.outbox), 2)
        self.assertFalse(User.objects.get(username='inviteuser').is_active)
        msg = mail.outbox[1]
        url = re.findall('(https?://\S+)', msg.body)[0]
        self.assert_email_appears_valid(mail.outbox[0])
        self.assert_email_appears_valid(mail.outbox[1])

        # Activate account
        anon_user.get(url)
        user = User.objects.get(username='inviteuser')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.get_all_permissions(), set())
        # User will NOT have any department object-level permissions for the inviting department
        self.assertFalse(fd.is_curator(user))
        self.assertFalse(fd.is_admin(user))

    def test_cancel_invitation(self):
        fd = self.load_la_department()

        dept_user = Client()
        anon_user = Client()
        fd.add_admin(self.non_admin_user)
        dept_user.login(**self.non_admin_creds)

        # Create invitation to test
        resp = dept_user.post(reverse('invitations:send-json-invite'), data=json.dumps([dict(department_id=fd.id, email='joe@test.com')]), content_type='application/json')

        invitation = fd.departmentinvitation_set.first().invitation

        # If invitation already accepted, return 401
        invitation.accepted = True
        invitation.save()
        resp = dept_user.post(
            reverse('invitations:cancel-invite', kwargs={'pk': invitation.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 401)

        # If user isn't an admin in the department, return 401
        invitation.accepted = False
        invitation.save()
        fd.remove_admin(self.non_admin_user)
        resp = dept_user.post(
            reverse('invitations:cancel-invite', kwargs={'pk': invitation.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 401)

        # Deleting invitation with admin permissions
        fd.add_admin(self.non_admin_user)
        resp = dept_user.post(
            reverse('invitations:cancel-invite', kwargs={'pk': invitation.id}),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)

        # After deleting, invitation link should not be available
        # Extract invite link from outbound email
        msg = mail.outbox[0]
        self.assert_email_appears_valid(mail.outbox[0])
        self.assertIn('non_admin@example.com', msg.body)
        self.assertIn('/invitations/accept-invite/', msg.body)
        url = re.findall('(https?://\S+)', msg.body)[0]
        path = urlparse(url).path
        resp = anon_user.get(path)
        # without enabling settings.INVITATIONS_GONE_ON_ACCEPT_ERROR, return 410
        # self.assertEqual(resp.status_code, 410)
        self.assert_redirect_to_login(resp)

    def test_predetermined_user_import(self):
        FireDepartment.objects.get_or_create(id=77549, name='FD1')
        FireDepartment.objects.get_or_create(id=92723, name='FD2')
        FireDepartment.objects.get_or_create(id=85484, name='FD3')
        FireDepartment.objects.get_or_create(id=81147, name='FD4')

        call_command('import-predetermined-admins', 'firecares/firecares_core/tests/mocks/predetermined_users.csv', stdout=StringIO())
        self.assertEqual(PredeterminedUser.objects.count(), 4)

        # Ensure that running the import again doesn't add more records...
        call_command('import-predetermined-admins', 'firecares/firecares_core/tests/mocks/predetermined_users.csv', stdout=StringIO())
        self.assertEqual(PredeterminedUser.objects.count(), 4)

    def test_predetermined_internal_registration(self):
        fd, _ = FireDepartment.objects.get_or_create(id=77549, name='FD1')
        fd2, _ = FireDepartment.objects.get_or_create(id=92723, name='FD2')
        FireDepartment.objects.get_or_create(id=85484, name='FD3')
        FireDepartment.objects.get_or_create(id=81147, name='FD4')

        call_command('import-predetermined-admins', 'firecares/firecares_core/tests/mocks/predetermined_users.csv', stdout=StringIO())

        c = Client()

        # Test association through internal registration system
        resp = c.post(reverse('account_request'), dict(email='testing@atlantaga.gov'))
        # This address should be whitelisted since it was loaded into the PredeterminedUser table
        self.assert_redirect_to(resp, 'registration_register')

        resp = c.post(reverse('registration_register'), data={'username': 'test_predetermined_reg',
                                                              'first_name': 'Joe',
                                                              'last_name': 'Tester',
                                                              'password1': 'test',
                                                              'password2': 'test'})
        user = User.objects.filter(username='test_predetermined_reg').first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_superuser)
        with self.settings(ADMINS=(('Test Admin', 'admin@example.com'),)):
            # Make sure that account activation triggers the department permission association
            response = c.get(reverse('registration_activate', kwargs={'activation_key':
                                                                      user.registrationprofile.activation_key}))
            # A 302 here means the activation succeeded
            self.assertEqual(response.status_code, 302)
            # 1 activation email to user, 1 notification to admins that a department admin account was activated
            self.assertEqual(len(mail.outbox), 2)
            map(self.assert_email_appears_valid, mail.outbox)
            msg = next(iter(filter(lambda x: 'admin@example.com' in x.recipients(), mail.outbox)), None)
            self.assertIsNotNone(msg)

        # User should ONLY have admin permissions on the department they were associated with during the import
        user.refresh_from_db()
        # In addition to becoming an admin on the department, the department association is saved to
        # the user's UserProfile
        self.assertEqual(user.userprofile.department, fd)
        self.assertTrue(fd.is_admin(user))
        self.assertFalse(fd.is_curator(user))
        self.assertFalse(fd2.is_admin(user))
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_department_whitelisted_registration(self):
        fd, _ = FireDepartment.objects.get_or_create(name='FD1')
        fd2, _ = FireDepartment.objects.get_or_create(name='FD2')
        RegistrationWhitelist.objects.create(email_or_domain='myfd.org', department=fd)
        RegistrationWhitelist.objects.create(email_or_domain='test@anotherfd.org', department=fd2, permission='admin_firedepartment,change_firedepartment')

        c = Client()

        resp = c.post(reverse('account_request'), dict(email='person@myfd.org'))
        self.assert_redirect_to(resp, 'registration_register')

        resp = c.post(reverse('registration_register'), data={'username': 'test_dept_whitelist',
                                                              'first_name': 'Joe',
                                                              'last_name': 'Tester',
                                                              'password1': 'test',
                                                              'password2': 'test'})
        user = User.objects.filter(username='test_dept_whitelist').first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_superuser)
        with self.settings(ADMINS=(('Test Admin', 'admin@example.com'),)):
            # Make sure that account activation triggers the department association
            response = c.get(reverse('registration_activate', kwargs={'activation_key':
                                                                      user.registrationprofile.activation_key}))
            # A 302 here means the activation succeeded
            self.assertEqual(response.status_code, 302)
            user.refresh_from_db()
            self.assertEqual(user.userprofile.department, fd)
            # Users might be associated with departments, but they will NOT get any department-related permissions
            # when being added to the department email whitelist unless explicitly indicated in the whitelisted entry
            self.assertFalse(fd.is_admin(user))
            self.assertFalse(fd.is_curator(user))
            # Ensure no permission crosstalk
            self.assertFalse(fd2.is_admin(user))
            self.assertFalse(fd2.is_curator(user))
            self.assertFalse(user.is_superuser)

        c.logout()

        # Ensure that permissions are assigned correctly when registering with a whitelisted address that has
        # permissions indicated
        resp = c.post(reverse('account_request'), dict(email='test@anotherfd.org'))
        self.assert_redirect_to(resp, 'registration_register')

        resp = c.post(reverse('registration_register'), data={'username': 'test_dept_whitelist2',
                                                              'first_name': 'Joe',
                                                              'last_name': 'Tester',
                                                              'password1': 'test',
                                                              'password2': 'test'})

        user = User.objects.filter(username='test_dept_whitelist2').first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_superuser)

        # Make sure that account activation triggers the department association
        response = c.get(reverse('registration_activate', kwargs={'activation_key':
                                                                  user.registrationprofile.activation_key}))
        # A 302 here means the activation succeeded
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.userprofile.department, fd2)

        self.assertTrue(fd2.is_admin(user))
        self.assertTrue(fd2.is_curator(user))
        # Ensure no permission crosstalk
        self.assertFalse(fd.is_admin(user))
        self.assertFalse(fd.is_curator(user))
        self.assertFalse(user.is_superuser)

    def test_department_admin_requests(self):
        fd, _ = FireDepartment.objects.get_or_create(id=12345, name='FD1')
        fd2, _ = FireDepartment.objects.get_or_create(id=12346, name='FD2')

        c = Client()

        # Need to at-least be logged in to get to this page...
        resp = c.get(reverse('registration_choose_department'))
        self.assert_redirect_to_login(resp)

        c.login(**self.non_admin_creds)
        resp = c.get(reverse('registration_choose_department'))

        self.assertEqual(resp.status_code, 200)

        with self.settings(DEPARTMENT_ADMIN_VERIFIERS=(('Test Admin', 'admin@example.com'),)):
            resp = c.post(reverse('registration_choose_department'), data={'state': 'MO', 'department': 12345})
            self.assert_redirect_to(resp, 'show_message')

            # Email for DEPARTMENT_ADMIN_VERIFIERS
            self.assertTrue(len(mail.outbox), 1)
            self.assert_email_appears_valid(mail.outbox[0])
            self.assertEqual(mail.outbox[0].recipients(), ['admin@example.com'])
            self.assertTrue('/accounts/verify-association-request/?email=non_admin@example.com' in mail.outbox[0].body)

        req = DepartmentAssociationRequest.objects.filter(user=self.non_admin_user, department=fd).first()
        self.assertIsNotNone(req)
        self.assertFalse(req.user.is_superuser)
        self.assertFalse(fd.is_admin(req.user))
        self.assertFalse(fd.is_curator(req.user))
        self.assertFalse(fd2.is_admin(req.user))
        self.assertFalse(req.is_denied)
        self.assertFalse(req.is_approved)

        c2 = Client()
        c2.login(**self.non_admin_creds)

        # Must be a superuser to get to the verification page
        resp = c2.get(reverse('verify-association-request'))
        self.assert_redirect_to_login(resp)

        c2.login(**self.admin_creds)
        resp = c2.get(reverse('verify-association-request') + '?email=' + self.non_admin_user.email)
        self.assertEqual(resp.status_code, 200)

        resp = c2.post(reverse('verify-association-request'), data=json.dumps({'id': req.id, 'approve': False, 'message': 'DENIED!!!'}), content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        # Test denial
        self.assertEqual(len(mail.outbox), 2)
        map(self.assert_email_appears_valid, mail.outbox)
        self.assertEqual(mail.outbox[1].recipients(), [req.user.email])
        self.assertTrue('DENIED!!!' in mail.outbox[1].body)
        self.non_admin_user.refresh_from_db()
        self.assertFalse(fd.is_admin(self.non_admin_user))
        self.assertFalse(fd.is_curator(self.non_admin_user))

        # Test approval
        resp = c.post(reverse('registration_choose_department'), data={'state': 'MO', 'department': 12346})
        req2 = DepartmentAssociationRequest.objects.filter(user=self.non_admin_user, department=fd2).first()
        self.assert_redirect_to(resp, 'show_message')
        resp = c2.post(reverse('verify-association-request'), data=json.dumps({'id': req2.id, 'approve': True, 'message': 'You are approved!'}), content_type='application/json')

        # We should have an admin on this department now
        self.non_admin_user.refresh_from_db()
        self.assertTrue(fd2.is_admin(self.non_admin_user))
        self.assertFalse(self.non_admin_user.is_superuser)
