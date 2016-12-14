import re
from logging import getLogger
from django.conf import settings
from django.contrib import auth, messages
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse, resolve
from django.http.response import HttpResponseRedirect
from zeep import Client

log = getLogger(__name__)


class DisclaimerAcceptedMiddleware(object):
    # Allow for login, logout and disclaimer views, all others redirect to disclaimer
    WHITELISTED_VIEWS = ['login', 'disclaimer', 'logout']

    def process_request(self, request):
        view_name = resolve(request.path).url_name
        # pass 404s through
        if not view_name or view_name in self.WHITELISTED_VIEWS:
            return None
        if request.user.is_authenticated() and not request.user.userprofile.has_accepted_terms:
            return HttpResponseRedirect(reverse('disclaimer') + '?next=' + request.path)


class IMISSingleSignOnMiddleware(object):
    application_instance = 1

    def __init__(self):
        self.imis = Client(settings.SSO_SERVICE_URL)

    def _extract_user_info(self, sso_user_container):
        ret = {i: getattr(sso_user_container, i) for i in sso_user_container if i != 'ExtensionData'}
        ret['extension_data'] = {x.tag: x.text for x in sso_user_container.ExtensionData._value_1}
        return ret

    def _create_username(self, user_info):
        return re.sub('[^a-zA-Z ]+', '', user_info.get('FullName').lower()).replace(' ', '.')

    def process_request(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django IMIS user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the IMISSingleSignOnMiddleware class.")
        # Looking to start a new session
        if 'ibcToken' in request.GET:
            # Verify token and create user if none exists
            token = request.GET['ibcToken']
            if self.imis.service.ValidateSession(applicationInstance=self.application_instance, userToken=token):
                request.session['ibcToken'] = token
                info = self.imis.service.FetchUserInfo(applicationInstance=self.application_instance, userToken=token)
                user_info = self._extract_user_info(info)

                user = auth.authenticate(remote_user=self._create_username(user_info))
                # Sync user information on every login
                if user:
                    user.email = user_info.get('EmailAddress', user.email)
                    user.first_name = user_info.get('FirstName', user.first_name)
                    user.last_name = user_info.get('LastName', user.last_name)
                    user.save()
                    # TODO: Handle department association if permissions are found
                    auth.login(request, user)
            else:
                messages.add_message(request, messages.ERROR, 'Invalid IMIS session token - {}'.format(token))
                return HttpResponseRedirect(reverse('login'))
