from django.test import override_settings
from django.test.client import Client
from django.core.urlresolvers import reverse
from firecares.firecares_core.tests.base import BaseFirecaresTestcase


class TestSlackFunctions(BaseFirecaresTestcase):
    @override_settings(SLACK_FIRECARES_COMMAND_TOKEN='test')
    def test_clear_cache(self):
        c = Client()
        c.login(**self.non_admin_creds)
        response = c.get(reverse('slack'))
        self.assertEqual(response.status_code, 405)

        data = dict(token='fail',
                    team_id='T0001',
                    team_domain='example',
                    channel_id='C2147483705',
                    channel_name='test',
                    user_id='U2147483697',
                    user_name='Steve',
                    command='/firecares',
                    text='clear_cache',
                    response_url='https://hooks.slack.com/commands/1234/5678')

        response = c.post(reverse('slack'), data)
        self.assertEqual(response.status_code, 403)

        data['token'] = 'test'
        response = c.post(reverse('slack'), data)
        self.assertEqual(response.status_code, 200)

        # sending an empty command should return help text
        data['text'] = ''
        response = c.post(reverse('slack'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/json')

        # "text" holds the command which must be whitelisted in the view.
        data['text'] = 'test'
        response = c.post(reverse('slack'), data)
        self.assertEqual(response.status_code, 403)
