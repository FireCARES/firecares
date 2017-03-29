from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test.client import Client
from StringIO import StringIO
from firecares.firecares_core.models import RegistrationWhitelist
from firecares.firecares_core.tests.base import BaseFirecaresTestcase
from firecares.firestation.models import FireDepartment, FireStation
from guardian.models import UserObjectPermission


class TestPublic(BaseFirecaresTestcase):

    def test_import_domain_names(self):
        """
        Ensures the import-domains command can do so by reading a csv roster file.
        """
        fd = FireDepartment.objects.create(name='Test', id=11111)
        call_command('import-domains', 'firecares/firestation/tests/mock/metro-roster.csv', stdout=StringIO())
        fd.refresh_from_db()
        self.assertEqual(fd.domain_name, 'fire.gov')

    def test_department_detail_view_does_not_require_login(self):
        """
        Ensures the department pages do not require login.
        """

        fd = FireDepartment.objects.create(name='Test db', population=0)
        c = Client()
        response = c.get(fd.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_department_list_view_does_not_require_login(self):
        """
        Ensures the department list view does not require login.
        """

        FireDepartment.objects.create(name='Test db', population=0)
        c = Client()
        response = c.get('/departments')
        self.assertEqual(response.status_code, 200)

    def test_firestation_detail_page_requires_login(self):
        """
        Ensures that the firestation detail page redirects to login for unauthoized users
        """

        fd = self.load_arlington_department()

        c = Client()

        fs = FireStation.objects.filter(department=fd).first()

        # Make sure that we're redirected to login since we're not yet authenticated
        response = c.get(reverse('firestation_detail', args=[fs.pk]))
        self.assert_redirect_to_login(response)
        response = c.get(reverse('firestation_detail_slug', args=[fs.pk, fs.slug]))
        self.assert_redirect_to_login(response)

        c.login(**self.admin_creds)

        # Make sure that we get back a valid page for both the regular route + slug route
        response = c.get(reverse('firestation_detail', args=[fs.pk]))
        self.assertEqual(response.status_code, 200)
        # Ensure that the slug works as well
        response = c.get(reverse('firestation_detail_slug', args=[fs.pk, fs.slug]))
        self.assertEqual(response.status_code, 200)

        # Any logged-in user should be able to see the fire station detail page...
        c.login(**self.non_admin_creds)

        # Make sure that we get back a valid page for both the regular route + slug route
        response = c.get(reverse('firestation_detail', args=[fs.pk]))
        self.assertEqual(response.status_code, 200)
        # Make sure that the user can't editing anything on the station...
        self.assertNotContains(response, 'onaftersave="updateStation()"')
        # Ensure that the slug works as well
        response = c.get(reverse('firestation_detail_slug', args=[fs.pk, fs.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'onaftersave="updateStation()"')

    def test_disclaimer(self):
        c = Client()

        response = c.get(reverse('disclaimer'))
        self.assert_redirect_to_login(response)

        # If we're logged in, we HAVE to accept the disclaimer on the next request (even if the page is public)
        # unless the URL has been whitelisted (login/logout/reset password workflow)
        c.login(**self.non_accepted_creds)
        response = c.get(reverse('firedepartment_list'))
        self.assert_redirect_to(response, 'disclaimer')

        response = c.post(reverse('disclaimer') + '?next=/departments/')
        self.assert_redirect_to(response, 'firedepartment_list')

        response = c.post(reverse('disclaimer'))
        self.assert_redirect_to(response, 'firestation_home')

    def test_public_does_not_see_safe_grades(self):
        c = Client()

        fd = self.load_arlington_department()

        # Anonymous users shouldn't see anything in the "Safe grades" area (besides a prompt to login)
        response = c.get(reverse('firedepartment_detail', args=[fd.pk]))
        self.assertNotContains(response, 'seconds over the industry standard.')
        self.assertNotContains(response, 'This department\'s performance score is')
        self.assertContains(response, 'to see this information')

        # Test the slug route as well...
        response = c.get(reverse('firedepartment_detail_slug', args=[fd.pk, fd.slug]))
        self.assertNotContains(response, 'seconds over the industry standard.')
        self.assertNotContains(response, 'This department\'s performance score is')
        self.assertContains(response, 'to see this information')

    def test_department_admin_page_access(self):
        c = Client()

        la_fd = self.load_la_department()

        # Ensure that anonymous users can't see any of the department admin pages
        response = c.get(reverse('firedepartment_update_government_units', args=[la_fd.pk]))
        self.assert_redirect_to_login(response)

        response = c.get(reverse('remove_intersecting_departments', args=[la_fd.pk]))
        self.assert_redirect_to_login(response)

        response = c.get(reverse('admin_department_users', args=[la_fd.pk]))
        self.assert_redirect_to_login(response)

        la_fd.add_curator(self.non_admin_user)
        c.login(**self.non_admin_creds)

        # Curators will be able to access department data admin pages...
        response = c.get(reverse('firedepartment_update_government_units', args=[la_fd.pk]))
        self.assertEqual(response.status_code, 200)

        response = c.get(reverse('remove_intersecting_departments', args=[la_fd.pk]))
        self.assertEqual(response.status_code, 200)

        # Curators cannot admin department users
        response = c.get(reverse('admin_department_users', args=[la_fd.pk]))
        self.assert_redirect_to_login(response)

        # Remove curator permissions and assign user admin permissions
        la_fd.remove_curator(self.non_admin_user)
        la_fd.add_admin(self.non_admin_user)

        # User admins can't see data management pages
        response = c.get(reverse('firedepartment_update_government_units', args=[la_fd.pk]))
        self.assert_redirect_to_login(response)

        response = c.get(reverse('remove_intersecting_departments', args=[la_fd.pk]))
        self.assert_redirect_to_login(response)

        # Admins can see the user admin page for a department...
        response = c.get(reverse('admin_department_users', args=[la_fd.pk]))
        self.assertEqual(response.status_code, 200)

    def test_cross_department_access(self):
        c = Client()

        la_fd = self.load_la_department()

        fd = self.load_arlington_department()

        fd.add_curator(self.non_admin_user)
        c.login(**self.non_admin_creds)

        # Shouldn't be able to access ANY of the data/user administration pages for the LA department
        response = c.get(reverse('firedepartment_update_government_units', args=[la_fd.pk]))
        self.assert_redirect_to_login(response)

        response = c.get(reverse('remove_intersecting_departments', args=[la_fd.pk]))
        self.assert_redirect_to_login(response)

        # Make admin on LA, but NOT on Arlington, shouldn't be able to access Arlington user admin
        la_fd.add_admin(self.non_admin_user)
        response = c.get(reverse('admin_department_users', args=[fd.pk]))
        self.assert_redirect_to_login(response)

    def test_station_inherited_permissions(self):
        c = Client()

        la_fd = self.load_la_department()
        station = la_fd.firestation_set.first()

        call_command('loaddata', 'firecares/firestation/fixtures/garner_fs.json', stdout=StringIO())
        garner_fs = FireStation.objects.get(id=5)

        c.login(**self.non_admin_creds)

        # No change_firedepartment yields no ability to update station data
        response = c.get(reverse('firestation_detail', args=[station.pk]))
        self.assertContains(response, 'draggable: false')
        self.assertNotContains(response, 'onaftersave="updateStation()"')
        response = c.get(reverse('firestation_detail_slug', args=[station.pk, station.slug]))
        self.assertContains(response, 'draggable: false')
        self.assertNotContains(response, 'onaftersave="updateStation()"')

        # Add the correct perm and ensure that the user would be able to change station detail
        la_fd.add_curator(self.non_admin_user)

        response = c.get(reverse('firestation_detail', args=[station.pk]))
        self.assertContains(response, 'draggable: true')
        self.assertContains(response, 'onaftersave="updateStation()"')
        response = c.get(reverse('firestation_detail_slug', args=[station.pk, station.slug]))
        self.assertContains(response, 'draggable: true')
        self.assertContains(response, 'onaftersave="updateStation()"')

        # Ensure that fire stations that DON'T have an associated fire department are still accessible to logged-in users
        response = c.get(reverse('firestation_detail', args=[garner_fs.pk]))
        self.assertEqual(response.status_code, 200)
        response = c.get(reverse('firestation_detail_slug', args=[garner_fs.pk, garner_fs.slug]))
        self.assertEqual(response.status_code, 200)

        c.logout()
        response = c.get(reverse('firestation_detail', args=[garner_fs.pk]))
        self.assert_redirect_to_login(response)
        response = c.get(reverse('firestation_detail_slug', args=[garner_fs.pk, garner_fs.slug]))
        self.assert_redirect_to_login(response)

    def test_orphaned_permissions_removed(self):
        fd = self.load_arlington_department()

        fd.add_curator(self.non_admin_user)
        perm = UserObjectPermission.objects.filter(user=self.non_admin_user).first()
        self.assertIsNotNone(perm)

        self.non_admin_user.delete()

        # Any permissions associated with this user should be gone
        perm = UserObjectPermission.objects.filter(user=self.non_admin_user).first()
        self.assertIsNone(perm)

    def test_ensure_correct_apparatus_component_renders(self):
        fd = self.load_arlington_department()
        station = fd.firestation_set.get(id=53534)

        c = Client()
        c.login(**self.non_admin_creds)

        # No change_firedepartment yields no ability to update station data
        response = c.get(reverse('firestation_detail', args=[station.pk]))
        self.assertContains(response, 'draggable: false')
        self.assertContains(response, 'staffed with <strong>{{ form.personnel }}</strong> personnel')
        self.assertNotContains(response, 'onaftersave="updateStation()"')
        response = c.get(reverse('firestation_detail_slug', args=[station.pk, station.slug]))
        self.assertContains(response, 'draggable: false')
        self.assertContains(response, 'staffed with <strong>{{ form.personnel }}</strong> personnel')
        self.assertNotContains(response, 'onaftersave="updateStation()"')

        # Add the correct perm and ensure that the user would be able to change station detail
        fd.add_curator(self.non_admin_user)

        response = c.get(reverse('firestation_detail', args=[station.pk]))
        self.assertContains(response, 'draggable: true')
        self.assertContains(response, 'onaftersave="updateStation()"')
        response = c.get(reverse('firestation_detail_slug', args=[station.pk, station.slug]))
        self.assertContains(response, 'draggable: true')
        self.assertContains(response, 'onaftersave="updateStation()"')

    def test_department_user_admin(self):
        fd = self.load_la_department()
        user, creds = self.create_test_user('user2', 'user2', email="user2@example.com")

        c = Client()
        c.login(**self.admin_creds)
        perms = {'can_change': ['non_admin@example.com', 'user2@example.com'], 'can_admin': 'non_admin@example.com', 'form': 'users'}

        resp = c.post(reverse('admin_department_users', args=[fd.id]), data=perms)
        self.assert_redirect_to(resp, 'firedepartment_detail_slug')
        self.assertTrue(fd.is_curator(user))
        self.assertFalse(fd.is_admin(user))
        self.assertTrue(fd.is_curator(self.non_admin_user))
        self.assertTrue(fd.is_admin(self.non_admin_user))

        # Ensure that permission deletion works as well
        perms = {'can_change': ['non_admin@example.com'], 'can_admin': 'non_admin@example.com', 'form': 'users'}

        resp = c.post(reverse('admin_department_users', args=[fd.id]), data=perms)
        self.assertFalse(fd.is_curator(user))

    def test_department_whitelist_admin(self):
        fd = self.load_la_department()

        c = Client()
        c.login(**self.admin_creds)

        whitelists = {'email_or_domain': ['test.com', 'test2@tester.com'], 'id': ['', ''], 'give_admin': ['false', 'true'], 'give_curator': ['false', 'true'], 'form': 'whitelist'}
        resp = c.post(reverse('admin_department_users', args=[fd.id]), data=whitelists)

        # We've got an individual whitelist email address added, so make sure that an email went out
        self.assertEqual(len(mail.outbox), 1)
        self.assert_email_appears_valid(mail.outbox[0])
        self.assertTrue('email address (test2@tester.com) has been whitelisted' in mail.outbox[0].body)

        self.assert_redirect_to(resp, 'firedepartment_detail_slug')

        self.assertTrue(RegistrationWhitelist.is_department_whitelisted('test.com'))
        self.assertEqual(RegistrationWhitelist.get_department_for_email('test.com'), fd)
        reg = RegistrationWhitelist.get_for_email('test2@tester.com')
        self.assertEqual(reg.department, fd)
        self.assertEqual(reg.permission, 'change_firedepartment,admin_firedepartment')

        # Ensure that deletion works as well
        whitelists = {'email_or_domain': ['test2@tester.com'], 'id': [''], 'form': 'whitelist'}
        resp = c.post(reverse('admin_department_users', args=[fd.id]), data=whitelists)

        self.assertFalse(RegistrationWhitelist.is_department_whitelisted('test.com'))
        self.assertIsNone(RegistrationWhitelist.get_department_for_email('test.com'))
