from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('username', help='Username for new user')
        parser.add_argument('password', help='Password for new user')
        parser.add_argument('email', help='User\'s email address')

        parser.add_argument('--superuser', action='store_true', default=False, help='Create user as a super user.',
                            dest='is_superuser'),
        parser.add_argument('--staff', action='store_true', default=False, help='Create user as staff.',
                            dest='is_staff'),
        parser.add_argument('--inactive', action='store_false', default=True, help='Create user as staff.',
                            dest='is_active'),

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