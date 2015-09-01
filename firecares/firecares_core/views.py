from django.http import HttpResponseRedirect
from django.views.generic import View
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from .forms import ForgotUsernameForm
from django.template.loader import render_to_string

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
                form.send_mail('Your Firecares Username',
                               'registration/forgot_username_email.txt',
                               context,
                               settings.DEFAULT_FROM_EMAIL,
                               user.email)
            return HttpResponseRedirect(reverse('username_sent'))
        return render(request, self.template_name, {'form': form})

class UsernameSent(View):
    template_name = 'registration/username_sent.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
