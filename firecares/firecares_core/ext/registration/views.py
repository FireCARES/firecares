from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.views.generic.edit import FormView
from registration.backends.default.views import RegistrationView
from firecares.firecares_core.models import RegistrationWhitelist
from firecares.firecares_core.forms import AccountRequestForm


UserModel = get_user_model()
SESSION_EMAIL_WHITELISTED = 'email_whitelisted'


class PreRegistrationCheckView(FormView):
    template_name = 'registration/registration_preregister.html'
    form_class = AccountRequestForm

    def form_valid(self, form):
        if RegistrationWhitelist.is_whitelisted(form.data.get('email')):
            self.request.session[SESSION_EMAIL_WHITELISTED] = form.data.get('email')
            return redirect('registration_register')
        else:
            form.save()
            return redirect('show_message')


class LimitedRegistrationView(RegistrationView):
    def dispatch(self, request, *args, **kwargs):
        if 'email_whitelisted' not in request.session:
            return redirect('registration_preregister')
        else:
            return super(LimitedRegistrationView, self).dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        kwargs = self.get_form_kwargs()
        if 'data' in kwargs:
            # Force email to come from session
            data = kwargs.get('data').copy()
            data['email'] = self.request.session[SESSION_EMAIL_WHITELISTED]
            kwargs['data'] = data

        ret = form_class(**kwargs)
        return ret

    def get_initial(self):
        initial = super(LimitedRegistrationView, self).get_initial()
        initial['email'] = self.request.session.get(SESSION_EMAIL_WHITELISTED)
        return initial
