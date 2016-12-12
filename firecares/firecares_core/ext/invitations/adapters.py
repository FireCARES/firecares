from invitations.adapters import BaseInvitationsAdapter
from registration.signals import user_registered


class DepartmentInvitationsAdapter(BaseInvitationsAdapter):
    def get_user_signed_up_signal(self):
        return user_registered
