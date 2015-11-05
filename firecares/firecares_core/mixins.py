import hashlib
import logging
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.cache import caches

logger = logging.getLogger(__name__)


def hash_for_cache(perms, page):
    return '_' + hashlib.md5((perms or '') + page).hexdigest() + '_'


class CacheMixin(object):
    """
    Caches class based views.
    """
    cache_timeout = 60
    cache_permission_differentiators = []

    def get_cache_timeout(self):
        return self.cache_timeout

    def get_permission_differentiators(self):
        return self.cache_permission_differentiators

    def dispatch(self, *args, **kwargs):
        request = args[0]
        perms = ','.join(request.user.get_all_permissions() & set(self.get_permission_differentiators()))
        return cache_page(self.get_cache_timeout(), key_prefix=hash_for_cache(perms, request.path))(super(CacheMixin, self).dispatch)(*args, **kwargs)


class LoginRequiredMixin(object):
    """
    Requires users to be logged in before rendering a view.
    """

    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)
