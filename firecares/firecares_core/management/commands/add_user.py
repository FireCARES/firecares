from django.core.management.base import BaseCommand
from optparse import make_option
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--username',
            action='store',
            default=None,
            help='Username for new user'),
        make_option('--password',
            action='store',
            default=None,
            help='User Password'),
        make_option('--email',
            action='store',
            default=None,
            help='User Email Address'),
        make_option('--is_superuser',
            action='store',
            default=False,
            help='Create user as a super user.'),
        make_option('--is_staff',
            action='store',
            default=False,
            help='Create user as staff.'),
        make_option('--is_active',
            action='store',
            default=True,
            help='Create user as staff.'),
        )

    def handle(self, *args, **kwargs):
        users_params = dict(username=kwargs.get('username'),
                            email=kwargs.get('email'),
                            is_superuser=kwargs.get('is_superuser'),
                            is_staff=kwargs.get('is_staff'),
                            is_active=kwargs.get('is_active')
                            )

        try:
            user, created = get_user_model().objects.get_or_create(**users_params)
        except IntegrityError:
            self.stdout.write('User: {0} already exists.'.format(kwargs.get('username')))
            return

        if created:
            user.set_password(kwargs.get('password').strip())
            user.save()
            self.stdout.write('Successfully created new user: {0}.'.format(user.username))

        else:
            self.stdout.write('User: {0} already exists.'.format(user.username))