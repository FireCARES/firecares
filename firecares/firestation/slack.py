import logging

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils.decorators import method_decorator
from firecares.tasks.cache import clear_cache
from firecares.tasks.slack import send_slack_message

logger = logging.getLogger(__name__)


class FireCARESSlack(View):
    """
    Class that routes and executes Slack commands.
    """
    http_method_names = ['post']
    commands = ['clear_cache']

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(FireCARESSlack, self).dispatch(*args, **kwargs)
    
    def clear_cache(self, request, *args, **kwargs):
        response_url = self.request.POST.get('response_url')
        clear_cache.delay(link=send_slack_message.s(response_url, {'text': 'Cache successfully cleared!'}),
                          link_error=send_slack_message.s(response_url, {'text': 'Cache clearing cache.'}))
        return HttpResponse()

    @staticmethod
    def parse_command(text):
        return text.split()[0]

    def command_dispatch(self, request, *args, **kwargs):
        command = self.parse_command(request.POST.get('text'))

        if command.lower() in self.commands:
            handler = getattr(self, command.lower(), self.command_not_allowed)
        else:
            handler = self.command_not_allowed

        return handler(request, *args, **kwargs)

    def command_not_allowed(self, request, *args, **kwargs):
        logger.warning('Command Not Allowed (%s): %s', self.parse_command(request.POST.get('text')), request.path,
            extra={'status_code': 403, 'request': request}
        )
        return HttpResponseForbidden(self._allowed_commands())

    @property
    def valid_token(self):
        """
        Validates the slack token against the one in settings.
        """
        return self.request.POST.get('token') == getattr(settings, 'SLACK_FIRECARES_COMMAND_TOKEN', '')

    def _allowed_commands(self):
        return [m.upper() for m in self.commands if hasattr(self, m)]

    def post(self, request, *args, **kwargs):

        if not self.valid_token:
            return HttpResponseForbidden('Invalid token.')

        return self.command_dispatch(request)

