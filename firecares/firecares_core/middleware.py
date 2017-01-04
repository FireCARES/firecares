import json
import requests
from logging import getLogger
from django.conf import settings
from django.contrib import auth, messages
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse, resolve
from django.http.response import HttpResponseRedirect, HttpResponseBadRequest
from zeep import Client
from requests_oauthlib import OAuth2Session
from oauthlib.common import to_unicode

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


def helix_token_compliance_hook(request):
    # "expires" value in response is causing collisions with "expires_in" w/in OAuthlib
    # and is of the wrong format for what appears to be backwards compabilitiy w/in OAuthlib
    # see https://github.com/idan/oauthlib/blob/master/oauthlib/oauth2/rfc6749/parameters.py#L370
    if request.status_code == 200:
        j = request.json()
        if 'expires' in j:
            j.pop('expires')
            request._content = to_unicode(json.dumps(j)).encode('UTF-8')

    return request


# TODO: This really should be a separate view vs middleware...
class OAuth2SingleSignOnMiddleware(object):
    def _whoami(self, token):
        return requests.get(settings.HELIX_WHOAMI, headers={'Authorization': 'Bearer ' + token.get('access_token')}).json()

    def _create_username(self, token):
        return 'iafc-{}'.format(token['username'])

    def process_request(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django HELIX user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the HelixSingleSignOnMiddleware class.")

        if 'code' in request.GET and 'state' in request.GET:
            # Respond to oauth2 workflow (grab a token)
            if request.session.get('oauth_state') != request.GET['state']:
                return HttpResponseBadRequest()

            redirect_uri = getattr(settings, 'HELIX_REDIRECT', request.build_absolute_uri('/'))
            oauth = OAuth2Session(settings.HELIX_CLIENT_ID, state=request.session['oauth_state'], redirect_uri=redirect_uri)
            oauth.register_compliance_hook('access_token_response', helix_token_compliance_hook)
            token = oauth.fetch_token(settings.HELIX_TOKEN_URL,
                                      client_secret=settings.HELIX_SECRET,
                                      code=request.GET['code'])
            request.session['oauth_token'] = token

            user = auth.authenticate(remote_user=self._create_username(token))

            if user:
                # TODO: Handle department association
                user.email = token.get('email')
                user.first_name = token.get('firstname')
                user.last_name = token.get('lastname')
                user.save()

                auth.login(request, user)


class IMISSingleSignOnMiddleware(object):
    application_instance = 1

    def __init__(self):
        self.imis = None

    def _extract_user_info(self, sso_user_container):
        ret = {i: getattr(sso_user_container, i) for i in sso_user_container if i != 'ExtensionData'}
        ret['extension_data'] = {x.tag: x.text for x in sso_user_container.ExtensionData._value_1}
        return ret

    def _create_username(self, user_info):
        return 'iaff-{}'.format(user_info.get('ImisId'))

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
            # Do service reflection on demand vs on middleware init
            self.imis = Client(settings.IMIS_SSO_SERVICE_URL) if not self.imis else self.imis
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
