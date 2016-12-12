import json
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.validators import validate_email
from django.http import HttpResponse
from invitations.exceptions import AlreadyInvited, AlreadyAccepted, UserRegisteredEmail
from invitations.forms import CleanEmailMixin
from invitations.models import Invitation
from invitations.views import SendJSONInvite, AcceptInvite
from firecares.firecares_core.ext.registration.views import SESSION_EMAIL_WHITELISTED
from firecares.firestation.models import FireDepartment


class SendJSONDepartmentInvite(SendJSONInvite):
    def post(self, request, *args, **kwargs):
        status_code = 400
        invites = json.loads(request.body.decode())
        response = {'valid': [], 'invalid': []}
        if isinstance(invites, list):
            for invite in invites:
                try:
                    invitee = invite.get('email')
                    dept_id = int(invite.get('department_id'))

                    validate_email(invitee)
                    CleanEmailMixin().validate_invitation(invitee)

                    dept = FireDepartment.objects.get(id=dept_id)
                    if not request.user.has_perm('admin_firedepartment', dept):
                        raise PermissionDenied()

                    i = Invitation.create(invitee, inviter=request.user)
                    i.departmentinvitation.department = dept
                    i.departmentinvitation.save()
                except(ValueError, KeyError):
                    pass
                except(PermissionDenied):
                    status_code = 401
                except(ValidationError):
                    response['invalid'].append({
                        invitee: 'Invalid email address'})
                except(AlreadyAccepted):
                    response['invalid'].append({
                        invitee: 'A user with this email has already accepted'})
                except(AlreadyInvited):
                    response['invalid'].append(
                        {invitee: 'An invite has already been sent for this user'})
                except(UserRegisteredEmail):
                    response['invalid'].append(
                        {invitee: 'A registered user with this email address already exists'})
                else:
                    i.send_invitation(request)
                    response['valid'].append({invitee: 'invited'})

        if response['valid']:
            status_code = 201

        return HttpResponse(
            json.dumps(response),
            status=status_code, content_type='application/json')


class AcceptDepartmentInvite(AcceptInvite):
    def post(self, request, *args, **kwargs):
        ret = super(AcceptDepartmentInvite, self).post(self, request, *args, **kwargs)
        # AOK to proceed if the email address was stashed, allow for preregistration check bypass
        if request.session['account_verified_email']:
            request.session[SESSION_EMAIL_WHITELISTED] = request.session['account_verified_email']
        return ret
