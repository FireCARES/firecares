import json
import requests
from .forms import ForgotUsernameForm, AccountRequestForm
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib import messages, auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.views import logout
from django.contrib.sites.models import Site
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, resolve_url
from django.template import loader
from django.views.generic import View, CreateView, TemplateView
from requests_oauthlib import OAuth2Session
from oauthlib.common import to_unicode
from zeep import Client
from guardian.shortcuts import get_objects_for_user
from firecares.tasks.email import send_mail, email_admins
from firecares.firestation.models import FireDepartment
from firecares.firecares_core.ext.registration.views import SESSION_EMAIL_WHITELISTED
from .forms import ContactForm
from .models import PredeterminedUser, RegistrationWhitelist, DepartmentAssociationRequest
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
            return redirect(reverse('username_sent'))
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
        return redirect(reverse('contact_thank_you'))

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
        kwargs['message_title'] = self.request.session.pop('message_title', 'Thanks!')
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
            messages.info(self.request, 'You already have an account on FireCARES.  If you\'ve forgotten your password or username, use the "Forgot Password or Username" links below.')
            return redirect('login')
        if RegistrationWhitelist.is_whitelisted(email):
            self.request.session[SESSION_EMAIL_WHITELISTED] = email
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
            self.request.session['message_title'] = 'Error'
            self.request.session['message'] = 'Error processing request.'
        return redirect('show_message')

    def send_email(self):
        """
        Email admins when new account requests are received.
        """

        # In the case that the account registration request is tied to a department,
        # we'll prompt the department admin to approve the request, which will send
        # an invite on the admin's behalf

        if self.object.department:
            to = [x.email for x in self.object.department.get_department_admins()]
            body = loader.render_to_string('contact/account_request_department_admin_email.txt', dict(contact=self.object, site=Site.objects.get_current()))
        else:
            to = [x[1] for x in settings.ADMINS]
            body = loader.render_to_string('contact/account_request_email.txt', dict(contact=self.object))
        email_message = EmailMultiAlternatives('{} - New account request received.'.format(Site.objects.get_current().name),
                                               body,
                                               settings.DEFAULT_FROM_EMAIL,
                                               to)
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


def get_functional_title(token):
    membershipid = token.get('membershipid')
    auth = {'Authorization': 'Bearer ' + token.get('access_token')}
    resp = requests.get(settings.HELIX_FUNCTIONAL_TITLE_URL + membershipid, headers=auth)
    return resp.content.strip('"')


class OAuth2Callback(View):
    def _whoami(self, token):
        return requests.get(settings.HELIX_WHOAMI, headers={'Authorization': 'Bearer ' + token.get('access_token')}).json()

    def _create_username(self, token):
        return 'iafc-{}'.format(token['membershipid'])

    def _allowed_in(self, token):
        return token.get('membershipid') and get_functional_title(token) in settings.HELIX_ACCEPTED_CHIEF_ADMIN_TITLES

    def _auth_user(self, token):
        user = authenticate(remote_user=self._create_username(token))
        if user:
            user.email = token.get('email')
            user.first_name = token.get('firstname')
            user.last_name = token.get('lastname')
            user.save()

        return user

    def _gate(self, request):
        request.session['message_title'] = 'Login error'
        request.session['message'] = 'Only IAFC fire chiefs are allowed to login into FireCARES via the Helix authentication system'
        return redirect('show_message')

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

            email = token.get('email')

            # If the user logs in through Helix AND they are in the perdetermined user list, then assign admin perms
            if email in PredeterminedUser.objects.values_list('email', flat=True):
                user = self._auth_user(token)
                if user:
                    login(request, user)
                    pdu = PredeterminedUser.objects.get(email=email)
                    pdu.department.add_admin(user)
                    # Also, associate this department with the user explicitly in the user's profile
                    user.userprofile.department = pdu.department
                    user.userprofile.save()
                    email_admins('Department admin user activated: {}'.format(user.username),
                                 'Admin permissions automatically granted for {} ({}) on {} ({})'.format(user.username, user.email, pdu.department.name, pdu.department.id))
                    # Send to associated department on login
                    return redirect(reverse('firedepartment_detail', args=[user.userprofile.department.id]))
            else:
                if self._allowed_in(token):
                    user = self._auth_user(token)
                    if user:
                        login(request, user)
                        user.userprofile.functional_title = get_functional_title(token)
                        user.userprofile.save()
                        if not DepartmentAssociationRequest.user_has_association_request(user):
                            return redirect(reverse('registration_choose_department'))
                        else:
                            return redirect(request.GET.get('next') or reverse('firestation_home'))

                else:
                    return self._gate(request)

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


class IMISRedirect(View):
    application_instance = 1
    imis = None

    def _extract_user_info(self, sso_user_container):
        ret = {i: getattr(sso_user_container, i) for i in sso_user_container if i != 'ExtensionData'}
        ret['extension_data'] = {x.tag: x.text for x in sso_user_container.ExtensionData._value_1}
        return ret

    def _create_username(self, user_info):
        return 'iaff-{}'.format(user_info.get('ImisId'))

    def _is_member(self, user_info):
        ext = user_info.get('extension_data')
        if ext and 'member' in ext.get('security_role').lower():
            return True
        else:
            return False

    def _should_be_department_admin(self, user_info):
        ext = user_info.get('extension_data')
        if ext and self._is_member(user_info):
            security_role = ext.get('security_role', '').lower()
            if 'member' in security_role and 'local_officer' in security_role:
                return True

        return False

    def _get_firecares_id(self, user_info):
        ext = user_info.get('extension_data')
        if ext:
            return ext.get('firecares_id')

        return None

    def _is_whitelisted(self, user_info):
        email = user_info.get('EmailAddress', None)
        return RegistrationWhitelist.is_whitelisted(email)

    def get(self, request):
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

                if not self._is_whitelisted(user_info) and not self._should_be_department_admin(user_info):
                    messages.add_message(request, messages.ERROR, 'Must be approved by a local officer to login to FireCARES using IMIS')
                    return redirect(reverse('login'))

                if not self._is_member(user_info):
                    messages.add_message(request, messages.ERROR, 'Must be an approved IAFF member to login to FireCARES using IMIS')
                    return redirect(reverse('login'))

                user = auth.authenticate(remote_user=self._create_username(user_info))
                # Sync user information on every login
                if user:
                    user.email = user_info.get('EmailAddress', user.email)
                    user.first_name = user_info.get('FirstName', user.first_name)
                    user.last_name = user_info.get('LastName', user.last_name)
                    user.save()

                    deptid = self._get_firecares_id(user_info)
                    user.userprofile.department = FireDepartment.objects.filter(id=deptid).first()
                    user.userprofile.save()

                    if self._should_be_department_admin(user_info) and deptid:
                        # Remove existing department permissions
                        departments = get_objects_for_user(user, 'firestation.admin_firedepartment')
                        for department in departments:
                            if department.id != deptid:
                                department.remove_admin(user)
                                department.remove_curator(user)
                        # Make this user an admin on the their "firecares_id" department
                        fd = FireDepartment.objects.get(id=deptid)
                        fd.add_admin(user)
                        fd.add_curator(user)
                    auth.login(request, user)
                    return redirect(request.GET.get('next') or reverse('firestation_home'))

        messages.add_message(request, messages.ERROR, 'Invalid or missing IMIS session token')
        return redirect(reverse('login'))
