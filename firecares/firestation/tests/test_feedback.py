import json
import mock
import os
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import Client
from firecares.firestation.models import FireDepartment, FireStation, DataFeedback
from firecares.firecares_core.tests.base import BaseFirecaresTestcase

User = get_user_model()


class FeedbackTests(BaseFirecaresTestcase):
    @mock.patch('geopy.geocoders.base.urllib_urlopen')
    def test_feedback_form(self, urllib_urlopen):
        """
        Test the feedback form submission
        """

        c = urllib_urlopen.return_value
        c.read.return_value = open(os.path.join(os.path.dirname(__file__), 'mock/geocode.json')).read()
        c.headers.getparam.return_value = 'utf-8'

        c = Client()
        with self.settings(DATA_FEEDBACK_EMAILS=(('Test Admin', 'admin@example.com'),)):
            # Create fire department and fire station
            fd = FireDepartment.objects.create(name='Fire Department 1')
            fs = FireStation.create_station(department=fd, address_string='1', name='Fire Station 1')
            feedback_url = reverse('firedepartment_data_feedback_slug', kwargs={'pk': fd.id, 'slug': fd.slug})
            response = c.get(feedback_url)
            self.assert_redirect_to_login(response)

            # Test only post allowed
            c.login(**self.non_admin_creds)
            get_response = c.get(feedback_url)
            self.assertEqual(get_response.status_code, 405)

            # Test email sent
            response = c.post(feedback_url, {
                'department': fd.id,
                'firestation': fs.id,
                'user': self.non_admin_user.id,
                'message': 'This is a test'
            })
            self.assertEqual(response.status_code, 201)
            self.assertEqual(DataFeedback.objects.filter(department=fd, firestation=fs).count(), 1)
            self.assertEqual(len(mail.outbox), 1)
            self.assert_email_appears_valid(mail.outbox[0])
            self.assertListEqual(mail.outbox[0].reply_to, ['non_admin@example.com'])
            mail_body = mail.outbox[0].body
            self.assertTrue(fd.name in mail_body)
            self.assertTrue(fs.name in mail_body)
            self.assertTrue(self.non_admin_user.username in mail_body)
            self.assertTrue(self.non_admin_user.email in mail_body)
            self.assertTrue('This is a test' in mail_body)

            # Test without fire station
            response = c.post(feedback_url, {
                'department': fd.id,
                'user': self.non_admin_user.id,
                'message': 'This is a test'
            })
            self.assertEqual(len(mail.outbox), 2)
            self.assert_email_appears_valid(mail.outbox[1])
            self.assertTrue('Fire Station:' not in mail.outbox[1].body)

            # Test invalid data
            response = c.post(feedback_url, {
                'department': fd.id,
                'message': 'This is a test'
            })
            self.assertEqual(response.status_code, 400)
            self.assertTrue('user' in json.loads(response.content))
