from django.test.client import Client
from django.core.management import call_command
from django.core.urlresolvers import reverse
from firecares.firecares_core.tests.base import BaseFirecaresTestcase
from firecares.firestation.models import FireDepartment, FireStation


class TestPublic(BaseFirecaresTestcase):
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

        call_command('loaddata', 'firecares/firestation/fixtures/test_firestation_detail.json')

        c = Client()

        fs = FireStation.objects.filter(id=46971).first()

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
