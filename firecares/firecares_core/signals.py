from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from guardian.models import UserObjectPermission, GroupObjectPermission
from invitations.signals import invite_accepted
from invitations.models import Invitation
from zeep import Client
from zeep.cache import InMemoryCache
from zeep.transports import Transport
from registration.signals import user_activated
from firecares.firecares_core.models import PredeterminedUser, RegistrationWhitelist
from firecares.tasks.email import email_admins


@receiver(pre_delete, sender=get_user_model())
def remove_obj_perms_connected_with_user(sender, instance, **kwargs):
    filters = Q(content_type=ContentType.objects.get_for_model(instance),
                object_pk=instance.pk)
    UserObjectPermission.objects.filter(filters).delete()
    GroupObjectPermission.objects.filter(filters).delete()


@receiver(invite_accepted)
def accepted(sender, *args, **kwargs):
    # User has registered for an account through the invitation, invitation is
    # officially "accepted"
    email = kwargs.pop('email')
    invite = Invitation.objects.get(email=email)
    user = get_user_model().objects.get(email=email)
    invite.departmentinvitation.user = user
    invite.departmentinvitation.save()


@receiver(pre_delete, sender=Session)
def sessionend_handler(sender, **kwargs):
    # Ensure that if user logs out of FireCARES, then then his/her IMIS session
    # token is destroyed
    inst = kwargs.get('instance').get_decoded()
    if 'ibcToken' in inst:
        token = inst.get('ibcToken')
        transport = Transport(cache=InMemoryCache())
        imis = Client(settings.IMIS_SSO_SERVICE_URL, transport=transport)
        imis.service.DisposeSessionByUserToken(applicationInstance=1, userToken=token)


@receiver(user_activated)
def account_activated(sender, *args, **kwargs):
    # A user account has been activated, check to see if we need to auto-elevate his/her permissions...
    user = kwargs.get('user')
    if user.email in PredeterminedUser.objects.values_list('email', flat=True):
        pdu = PredeterminedUser.objects.get(email=user.email)
        pdu.department.add_admin(user)
        user.userprofile.department = pdu.department
        user.userprofile.save()
        email_admins('Department admin user activated: {}'.format(user.username),
                     'Admin permissions granted for {} ({}) on {} ({})'.format(user.username, user.email, pdu.department.name, pdu.department.id))

    if RegistrationWhitelist.is_department_whitelisted(user.email):
        wht = RegistrationWhitelist.get_for_email(user.email)
        if wht:
            wht.process_permission_assignment(user)

        user.userprofile.department = RegistrationWhitelist.get_department_for_email(user.email)
        user.userprofile.save()
