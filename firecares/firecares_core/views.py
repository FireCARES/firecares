import json
import requests
from .forms import ForgotUsernameForm, AccountRequestForm
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.views import logout
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, redirect, resolve_url
from django.template import loader
from django.views.generic import View, CreateView, TemplateView
from requests_oauthlib import OAuth2Session
from oauthlib.common import to_unicode
from firecares.tasks.email import send_mail
from .forms import ContactForm
from .models import RegistrationWhitelist
from .mixins import LoginRequiredMixin


class ForgotUsername(View):
    form_class = ForgotUsernameForm
    template_name = 'registration/forgot_username.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = User.objects.filter(email=form.cleaned_data['email']).first()
            if user:
                context = {'username': user.username,
                           'login': request.build_absolute_uri(reverse('login'))}
                form.send_mail('Your FireCARES Username',
                               'registration/forgot_username_email.txt',
                               context,
                               settings.DEFAULT_FROM_EMAIL,
                               user.email)
            return HttpResponseRedirect(reverse('username_sent'))
        return render(request, self.template_name, {'form': form})


class ContactUs(View):
    template_name = 'contact/contact.html'

    def send_email(self, contact):
        body = loader.render_to_string('contact/contact_admin_email.txt', dict(contact=contact))

        email_message = EmailMultiAlternatives('Contact request submitted',
                                               body,
                                               settings.DEFAULT_FROM_EMAIL,
                                               [x[1] for x in settings.ADMINS])
        send_mail.delay(email_message)

    def _save_and_notify(self, form):
        m = form.save()
        self.send_email(m)
        return HttpResponseRedirect(reverse('contact_thank_you'))

    def get(self, request, *args, **kwargs):
        form = ContactForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)

        if form.is_valid():
            if settings.RECAPTCHA_SECRET:
                data = {
                    'secret': settings.RECAPTCHA_SECRET,
                    'response': request.POST['g-recaptcha-response']
                }
                resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
                if resp.json()['success']:
                    return self._save_and_notify(form)
                else:
                    form.add_error(None, 'Robot check failed.  Did you check the "I\'m not a robot" checkbox?')
                    return render(request, self.template_name, {'form': form})
            else:
                # Captcha checking disabled
                return self._save_and_notify(form)
        return render(request, self.template_name, {'form': form})


class ShowMessage(TemplateView):
    """
    Generic view for showing messages to the user.

    Set message with via self.request.session['message'] = 'message_string'.
    """
    template_name = 'show_message.html'

    def get_context_data(self, **kwargs):
        kwargs['message'] = self.request.session.pop('message', 'Your submission has been received.')
        return super(ShowMessage, self).get_context_data(**kwargs)


class AccountRequestView(CreateView):
    """
    Processes account requests.
    """
    template_name = 'firestation/home.html'
    form_class = AccountRequestForm
    http_method_names = ['post']
    success_message = 'We will be in touch with you to verify your account. Please stay tuned to our partner websites'\
                      ' and major fire service conferences for updates.'

    def form_valid(self, form):
        """
        If the form is valid AND the email is whitelisted, then send to registration; otherwise capture email address.
        """
        email = form.data.get('email')
        if User.objects.filter(email=email).first():
            # Redirect to login if a user w/ that email has already been found
            return redirect('login')
        if RegistrationWhitelist.is_whitelisted(email):
            self.request.session['email_whitelisted'] = email
            return redirect('registration_register')
        else:
            self.object = form.save()
            self.send_email()
            self.request.session['message'] = self.success_message
            return redirect('show_message')

    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        if form.errors.get('email'):
            self.request.session['message'] = form.errors['email'][0]
        else:
            self.request.session['message'] = 'Error processing request.'
        return redirect('show_message')

    def send_email(self):
        """
        Email admins when new account requests are received.
        """
        body = loader.render_to_string('contact/account_request_email.txt', dict(contact=self.object))
        email_message = EmailMultiAlternatives('{} - New account request received.'.format(Site.objects.get_current().name),
                                               body,
                                               settings.DEFAULT_FROM_EMAIL,
                                               [x[1] for x in settings.ADMINS])
        send_mail.delay(email_message)


class Disclaimer(LoginRequiredMixin, TemplateView):
    template_name = 'disclaimer.html'

    def post(self, request, *args, **kwargs):
        profile = request.user.userprofile
        profile.has_accepted_terms = True
        profile.save()
        return redirect(request.GET.get('next') or reverse('firestation_home'))


class OAuth2Redirect(View):
    def get(self, request):
        # Start OAuth2 session
        redirect_uri = getattr(settings, 'HELIX_REDIRECT', request.build_absolute_uri(reverse('oauth_callback')))
        oauth = OAuth2Session(settings.HELIX_CLIENT_ID,
                              scope=settings.HELIX_SCOPE,
                              redirect_uri=redirect_uri)
        url, state = oauth.authorization_url(settings.HELIX_AUTHORIZE_URL)
        request.session['oauth_state'] = state
        return redirect(url)


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


class OAuth2Callback(View):
    def _whoami(self, token):
        return requests.get(settings.HELIX_WHOAMI, headers={'Authorization': 'Bearer ' + token.get('access_token')}).json()

    def _create_username(self, token):
        return 'iafc-{}'.format(token['username'])

    def get(self, request):
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

            user = authenticate(remote_user=self._create_username(token))

            if user:
                # TODO: Handle department association
                user.email = token.get('email')
                user.first_name = token.get('firstname')
                user.last_name = token.get('lastname')
                user.save()

                login(request, user)
                return redirect(request.GET.get('next') or reverse('firestation_home'))
        else:
            return HttpResponseBadRequest()


def sso_logout_then_login(request, login_url=None, current_app=None, extra_context=None):
    """
    Logs out the user if they are logged in. Then redirects to the log-in page OR
    to the SSO logout page (which redirects to the FireCARES login page).
    """
    if not login_url:
        login_url = settings.LOGIN_URL
    login_url = resolve_url(login_url)

    if 'oauth_token' in request.session:
        login_url = settings.HELIX_LOGOUT_URL
    return logout(request, login_url, current_app=current_app, extra_context=extra_context)
