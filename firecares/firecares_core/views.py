import requests
from .forms import ForgotUsernameForm, AccountRequestForm
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.template import loader
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, CreateView, TemplateView
from firecares.firecares_core.forms import ContactForm
from firecares.tasks.email import send_mail


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
    success_message = 'We will be in touch with you when FireCARES is ready. Please stay tuned to our partner websites'\
                      ' and major fire service conferences for updates.'

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save()
        self.send_email()
        self.request.session['message'] = self.success_message
        return HttpResponseRedirect(reverse('show_message'))

    def form_invalid(self, form):
        """
        If the form is invalid, re-render the context data with the
        data-filled form and errors.
        """
        if form.errors.get('email'):
            self.request.session['message'] = form.errors['email'][0]
        else:
            self.request.session['message'] = 'Error processing request.'
        return HttpResponseRedirect(reverse('show_message'))

    def send_email(self):
        """
        Email admins when new account requests are received.
        """
        body = loader.render_to_string('contact/account_request_email.txt', dict(contact=self.object))
        email_message = EmailMultiAlternatives('New account request received.',
                                               body,
                                               settings.DEFAULT_FROM_EMAIL,
                                               [x[1] for x in settings.ADMINS])
        send_mail.delay(email_message)
