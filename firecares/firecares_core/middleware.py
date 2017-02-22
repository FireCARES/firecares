import time
from logging import getLogger
from django.core.urlresolvers import reverse, resolve
from django.http.response import HttpResponseRedirect

log = getLogger(__name__)


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


class RequestDurationMiddleware(object):
    def process_request(self, request):
        self.start_time = time.time()

    def process_response(self, request, response):
        try:
            req_time = time.time() - self.start_time
            log.info("%s %s %s" % (response.status_code, request.method, request.get_full_path()), extra={'exec_time': req_time})
        except Exception, e:
            log.error("LoggingMiddleware Error: %s" % e)
        return response
