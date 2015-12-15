import requests
from .forms import ForgotUsernameForm
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.views.generic import View
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
