import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.humanize.templatetags import humanize
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.http.response import HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect
from django.template import loader
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from registration.backends.default.views import RegistrationView
from firecares.firecares_core.mixins import LoginRequiredMixin, SuperUserRequiredMixin
from firecares.firecares_core.models import PredeterminedUser, DepartmentAssociationRequest
from firecares.firecares_core.forms import AccountRequestForm
from firecares.firestation.models import FireDepartment
from firecares.tasks.email import send_mail
from .forms import ChooseDepartmentForm


UserModel = get_user_model()
SESSION_EMAIL_WHITELISTED = 'email_whitelisted'


class RegistrationPreregisterView(FormView):
    template_name = 'registration/registration_preregister.html'
    form_class = AccountRequestForm

    def get(self, request):
        if 'department' in request.GET:
            fd = FireDepartment.objects.get(id=request.GET['department'])
            admins = fd.get_department_admins()
            if not admins:
                request.session['message'] = 'We\'re sorry, a Fire Chief or Local Officer needs to enable FireCARES on this department before your account can be approved by the department.'
                request.session['message_title'] = 'FireCARES not enabled for {}'.format(fd.name)
                return redirect('show_message')
        return super(RegistrationPreregisterView, self).get(request)


class LimitedRegistrationView(RegistrationView):
    def dispatch(self, request, *args, **kwargs):
        if SESSION_EMAIL_WHITELISTED not in request.session:
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
        email = self.request.session.get(SESSION_EMAIL_WHITELISTED)
        initial['email'] = email
        # Pre-fill first name and last name for users that are from the predetermined admins...
        if email in PredeterminedUser.objects.values_list('email', flat=True):
            pdu = PredeterminedUser.objects.get(email=email)
            initial['first_name'] = pdu.first_name
            initial['last_name'] = pdu.last_name
        return initial


class ChooseDepartmentView(LoginRequiredMixin, FormView):
    template_name = 'registration/registration_choose_department.html'
    form_class = ChooseDepartmentForm

    def get_context_data(self, **kwargs):
        context = super(ChooseDepartmentView, self).get_context_data(**kwargs)
        context['states'] = list(FireDepartment.objects.exclude(state__isnull=True).exclude(archived=True).exclude(state__exact='').order_by('state').distinct('state').values_list('state', flat=True))
        return context

    def form_valid(self, form):
        department = FireDepartment.objects.get(id=form.data.get('department'))
        association = DepartmentAssociationRequest.objects.create(department=department, user=self.request.user)

        # Send email to DEPARTMENT_ADMIN_VERIFIERS
        context = dict(association=association, email=association.user.email, username=association.user.username, site=get_current_site(self.request))
        body = loader.render_to_string('registration/verify_admin_email.txt', context)
        subject = 'Department administrator request - {email}'.format(email=association.user.email)
        email_message = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, [x[1] for x in settings.DEPARTMENT_ADMIN_VERIFIERS])
        send_mail.delay(email_message)

        self.request.session['message'] = 'Your request has been received, an administrator will contact you shortly to verify your information.  In the meantime, feel free to peruse the FireCARES site!'
        return redirect('show_message')


def serialize_association_request(req):
    return dict(id=req.id,
                department=dict(name=req.department.name, state=req.department.state),
                approved_by=dict(name=req.approved_by.username, email=req.approved_by.email) if req.approved_by else None,
                denied_by=dict(name=req.denied_by.username, email=req.denied_by.email) if req.denied_by else None,
                permission=req.permission,
                approved_at=humanize.naturaltime(req.approved_at),
                denied_at=humanize.naturaltime(req.denied_at),
                is_approved=req.is_approved,
                is_denied=req.is_denied)


class VerifyAssociationRequest(SuperUserRequiredMixin, TemplateView):
    template_name = 'registration/verify_association_request.html'

    def get_context_data(self, **kwargs):
        context = super(VerifyAssociationRequest, self).get_context_data(**kwargs)
        email = self.request.GET.get('email')
        reqs = []
        for req in DepartmentAssociationRequest.filter_by_email(email).order_by('-created_at'):
            item = serialize_association_request(req)
            reqs.append(item)

        context['user'] = UserModel.objects.get(email=email)
        context['requests'] = reqs
        return context

    def get(self, request):
        email = request.GET.get('email')
        user = UserModel.objects.filter(email=email).first()
        if not email or user is None:
            return HttpResponseBadRequest('valid email address required')
        elif user.departmentassociationrequest_set.count() is 0:
            return HttpResponseNotFound('no requests with this email address')
        return super(VerifyAssociationRequest, self).get(request)

    def post(self, *args, **kwargs):
        body = json.loads(self.request.body)
        req = DepartmentAssociationRequest.objects.get(id=body.get('id'))
        if body.get('approve', False):
            req.approve(self.request.user)
        else:
            req.deny(self.request.user)

        # Send email reponse to requesting user of acceptance or denial
        context = dict(association=req, message=body.get('message'), site=get_current_site(self.request))
        body = loader.render_to_string('registration/association_response_email.txt', context)
        subject = 'Department administrator request'
        email_message = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, [req.user.email])
        send_mail.delay(email_message)

        req.refresh_from_db()

        return JsonResponse(serialize_association_request(req))
