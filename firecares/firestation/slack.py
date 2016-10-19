import logging

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils.decorators import method_decorator
from firecares.tasks.cache import clear_cache as clear_cache_task
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

    @property
    def help_text(self):
        """
        Returns a list of commands.
        """

        msg = """clear_cache: Nuclear option, clears the entire cache.
        """

        return {'text': msg}

    def clear_cache(self, request, *args, **kwargs):
        clear_cache_task.apply_async(link=send_slack_message.s(self.response_url, {'text': 'Cache successfully cleared!'}),
                                     link_error=send_slack_message.s(self.response_url, {'text': 'Cache clearing cache.'}))
        return HttpResponse()

    def parse_message(self):
        """
        Parses the incoming message from slack.
        """

        try:
            text = self.request.POST.get('text').split()
            self.command = text[0]
            self.command_args = text[1:]

        except IndexError:
            self.command = ''
            self.command_args = ''

        self.response_url = self.request.POST.get('response_url')
        self.token = self.request.POST.get('token')
        self.username = self.request.POST.get('user_name')
        self.user_id = self.request.POST.get('user_id')
        self.channel_name = self.request.POST.get('channel_name')
        self.channel_id = self.request.POST.get('channel_id')
        self.team_domain = self.request.POST.get('team_domain')
        self.team_id = self.request.POST.get('team_id')

    def command_dispatch(self, request, *args, **kwargs):
        command = self.command

        if not command:
            return JsonResponse(self.help_text)

        if command.lower() in self.commands:
            handler = getattr(self, command.lower(), self.command_not_allowed)
        else:
            handler = self.command_not_allowed

        return handler(request, *args, **kwargs)

    def command_not_allowed(self, request, *args, **kwargs):
        logger.warning('Command Not Allowed (%s): %s', self.command, request.path,
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

        self.parse_message()
        return self.command_dispatch(request)

