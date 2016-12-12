from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from guardian.models import UserObjectPermission, GroupObjectPermission
from invitations.signals import invite_accepted
from invitations.models import Invitation


@receiver(pre_delete, sender=get_user_model())
def remove_obj_perms_connected_with_user(sender, instance, **kwargs):
    filters = Q(content_type=ContentType.objects.get_for_model(instance),
                object_pk=instance.pk)
    UserObjectPermission.objects.filter(filters).delete()
    GroupObjectPermission.objects.filter(filters).delete()


@receiver(invite_accepted)
def accepted(sender, *args, **kwargs):
    # User has registered for an account through the invitation, invitation is
    # officially "accepted", assign correct department curator permissions now
    email = kwargs.pop('email')
    invite = Invitation.objects.get(email=email)
    department = invite.departmentinvitation.department
    user = get_user_model().objects.get(email=email)
    user.add_obj_perm('change_firedepartment', department)
    invite.departmentinvitation.user = user
    invite.departmentinvitation.save()
