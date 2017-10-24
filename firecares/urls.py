from autocomplete_light.views import RegistryView, AutocompleteView
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.defaults import page_not_found
from django.views.generic import TemplateView
from .firecares_core.forms import FirecaresPasswordResetForm
from .firecares_core.views import (ForgotUsername, ContactUs, AccountRequestView,
                                   ShowMessage, Disclaimer, OAuth2Callback,
                                   OAuth2Redirect, sso_logout_then_login, IMISRedirect,
                                   FAQView, TruncatedFileAddView)
from .firestation.api import StaffingResource, FireStationResource, FireDepartmentResource, WeatherWarningResource, StaffingStationRollupResource, GetServiceAreaInfo
from tastypie.api import Api
from firestation.views import Home
from osgeo_importer.urls import importer_api
from sitemaps import BaseSitemap, DepartmentsSitemap

admin.autodiscover()
v1_api = Api(api_name='v1')
v1_api.register(StaffingResource())
v1_api.register(FireStationResource())
v1_api.register(FireDepartmentResource())
v1_api.register(WeatherWarningResource())
v1_api.register(StaffingStationRollupResource())
v1_api.register(GetServiceAreaInfo())

sitemaps = {
    'base': BaseSitemap,
    'departments': DepartmentsSitemap,
}

urlpatterns = patterns('',
    url(r'^$', Home.as_view(), name='firestation_home'),  # noqa
    url(r'^(?i)IAFF/?$', Home.as_view(), name='firestation_iaff_home'),
    (r'^api/', include(v1_api.urls)),
    url(r'^', include('firecares.firestation.urls')),
    url(r'^contact-us/$', ContactUs.as_view(), name='contact_us'),
    url(r'^contact-us/thank-you/$', TemplateView.as_view(template_name='contact/thank_you.html'), name='contact_thank_you'),
    (r'^accounts/', include('firecares.firecares_core.ext.registration.urls')),
    url(r'^account-request/$', AccountRequestView.as_view(), name='account_request'),
    url(r'^thank-you/$', ShowMessage.as_view(), name='show_message'),
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
    url(r'^logout/$', sso_logout_then_login, name='logout'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^autocomplete/$', RegistryView.as_view(), name='autocomplete_light_registry'),
    url(r'^autocomplete/(?P<autocomplete>[-\w]+)/$', login_required(AutocompleteView.as_view()), name='autocomplete_light_autocomplete'),
    url(r'^robots\.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots.txt'),
    url(r'^faq/$', FAQView.as_view(), name='faq.html'),
    url(r'^sitemap\.xml$', include('static_sitemaps.urls')),

    url(r'^favit/', include('favit.urls')),

    # importer routes
    url(r'^uploads/new$', TruncatedFileAddView.as_view(), name='uploads-new'),
    url(r'^uploads/new/json$', TruncatedFileAddView.as_view(json=True), name='uploads-new-json'),

    # url(r'^uploads/?$', permission_required('change_firestation' UploadListView.as_view()), name='uploads-list'),
    url(r'', include(importer_api.urls)),
    url(r'^disclaimer/$', Disclaimer.as_view(), name='disclaimer'),
    url(r'^invitations/', include('firecares.firecares_core.ext.invitations.urls', namespace='invitations')),
    url(r'^oauth/$', OAuth2Callback.as_view(), name='oauth_callback'),
    url(r'^oauthlogin/$', OAuth2Redirect.as_view(), name='oauth_redirect'),
    url(r'^imis/$', IMISRedirect.as_view(), name='imis')
)

if settings.DEBUG:
    urlpatterns += patterns('', url(r'^.*/$', page_not_found),)
