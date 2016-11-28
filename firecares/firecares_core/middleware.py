from django.http.response import HttpResponseRedirect
from django.core.urlresolvers import reverse, resolve


class DisclaimerAcceptedMiddleware(object):
    # Allow for login, logout and disclaimer views, all others redirect to disclaimer
    WHITELISTED_VIEWS = ['login', 'disclaimer', 'logout']

    def process_request(self, request):
        view_name = resolve(request.path).url_name
        # pass 404s through
        if not view_name or view_name in self.WHITELISTED_VIEWS:
            return None
        if request.user.is_authenticated() and not request.user.userprofile.has_accepted_terms:
            return HttpResponseRedirect(reverse('disclaimer') + '?next=' + request.path)
