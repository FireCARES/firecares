import logging
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.utils.decorators import method_decorator
from firecares.tasks.cache import clear_cache as clear_cache_task
from firecares.tasks.slack import send_slack_message
from firecares.tasks.update import update_nfirs_counts, update_performance_score
from firecares.firecares_core.models import AccountRequest
from firecares.firestation.models import FireDepartment

logger = logging.getLogger(__name__)


class FireCARESSlack(View):
    """
    Class that routes and executes Slack commands.
    """
    http_method_names = ['post']
    commands = ['clear_cache', 'account_requests', 'update_nfirs_counts', 'update_performance_scores', 'q',
                'archive_department']

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(FireCARESSlack, self).dispatch(*args, **kwargs)

    @property
    def help_text(self):
        """
        Returns a list of commands.
        """

        msg = """*q*: Searches firecares for a department. (Args: [<query>])
        *clear_cache*: Nuclear option, clears the entire cache.
        *account_requests*: Returns the number of active account requests.
        *update_nfirs_counts*: Updates the annual residential fire and casualty counts for a department. (Args: [<department_id>])
        *update_performance_scores*: Updates the performance score for a department. (Args: [<department_id>])
        *archive_department:* Archive a department. (Args: [<department_id>])
        """

        return {'text': msg}

    def clear_cache(self, request, *args, **kwargs):
        clear_cache_task.apply_async(link=send_slack_message.s(self.response_url, {'text': 'Cache successfully cleared!'}),
                                     link_error=send_slack_message.s(self.response_url, {'text': 'Error clearing cache.'}))
        return HttpResponse()

    def account_requests(self, request, *args, **kwargs):
        return JsonResponse({'text': 'There are currently {0} pending account requests.'.format(AccountRequest.objects.count())})

    def update_nfirs_counts(self, request, *args, **kwargs):
        for department in self.command_args:
            update_nfirs_counts.apply_async((department,),
                                        link=send_slack_message.s(self.response_url, {'text': 'NFIRS counts updated for department: {}'.format(department)}),
                                        link_error=send_slack_message.s(self.response_url, {'text': 'Error updating NFIRS counts for department: {}'.format(department)}))
        return HttpResponse()

    def update_performance_scores(self, request, *args, **kwargs):
        for department in self.command_args:
            update_performance_score.apply_async((department,),
                                        link=send_slack_message.s(self.response_url, {'text': 'Performance score updated for department: {}'.format(department)}),
                                        link_error=send_slack_message.s(self.response_url, {'text': 'Error updating performance score for department: {}'.format(department)}))
        return HttpResponse()

    def q(self, request, *args, **kwargs):
        departments = FireDepartment.objects.filter(archived=False).full_text_search(' '.join(self.command_args))
        msg = ['{index}. <https://firecares.org{url}|{name}>, {state}'.format(index=n+1, name=department.name, url=department.get_absolute_url(), state=department.state) for n, department in enumerate(departments)]
        return JsonResponse({'text': '\n'.join(msg)})

    def archive_department(self, request, *args, **kwargs):

        if not self.command_args:
            return JsonResponse({'text': 'Missing argument.'}, status=400)

        departments = FireDepartment.objects.filter(id__in=self.command_args)
        departments.update(archived=True)
        msg = ['{index}. <https://firecares.org{url}|{name}> has been archived.'.format(index=n+1, name=department.name, url=department.get_absolute_url()) for n, department in enumerate(departments)]
        return JsonResponse({'text': '\n'.join(msg)})

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

