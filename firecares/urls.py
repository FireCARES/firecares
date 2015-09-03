from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from .firecares_core.forms import FirecaresPasswordResetForm
from .firestation.views import Home
from .firecares_core.views import ForgotUsername
from .firestation.api import StaffingResource, FireStationResource, FireDepartmentResource
from tastypie.api import Api
from firestation.views import Home

admin.autodiscover()
v1_api = Api(api_name='v1')
v1_api.register(StaffingResource())
v1_api.register(FireStationResource())
v1_api.register(FireDepartmentResource())


urlpatterns = patterns('',
    # Examples:
    url(r'^$', cache_page(60*15)(Home.as_view()), name='firestation_home'),
    (r'^api/', include(v1_api.urls)),
    url(r'^', include('firecares.firestation.urls')),
    (r'^accounts/', include('registration.backends.default.urls')),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login', kwargs={'template_name': 'accounts/login.html'}),
    url(r'^password-reset/$', 'django.contrib.auth.views.password_reset',
        name='password_reset',
        kwargs={'template_name': 'registration/password/password_reset_form.html',
                'password_reset_form': FirecaresPasswordResetForm}),
    url(r'^password-reset/done/$', 'django.contrib.auth.views.password_reset_done',
        name='password_reset_done',
        kwargs={'template_name': 'registration/password/password_reset_done.html'}),
    url(r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        'django.contrib.auth.views.password_reset_confirm', name='password_reset_confirm',
        kwargs={'template_name': 'registration/password/password_reset_confirm.html'}),
    url(r'^password-reset/complete/$', 'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete', kwargs={'template_name': 'registration/password/password_reset_complete.html'}),
    url(r'^password-change/$', 'django.contrib.auth.views.password_change', name='password_change',
        kwargs={'template_name': 'registration/password/password_change.html'}),
    url(r'^password-change/done/$', 'django.contrib.auth.views.password_change_done', name='password_change_done',
        kwargs={'template_name': 'registration/password/password_change_done.html'}),
    url(r'^forgot-username/$', ForgotUsername.as_view(), name='forgot_username'),
    url(r'^forgot-username/done/$', TemplateView.as_view(template_name='registration/username_sent.html'), name='username_sent'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
)
