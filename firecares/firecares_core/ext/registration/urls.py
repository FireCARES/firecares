from django.conf.urls import patterns, url
from registration.backends.default.urls import urlpatterns as reg_patterns
from .views import LimitedRegistrationView, PreRegistrationCheckView

urlpatterns = patterns('',
                       url(r'^registration-check/$',
                           PreRegistrationCheckView.as_view(),
                           name='registration_preregister'),
                       url(r'^register/$',
                           LimitedRegistrationView.as_view(),
                           name='registration_register'),)

urlpatterns += reg_patterns
