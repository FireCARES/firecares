from django.conf.urls import patterns, url
from registration.backends.default.urls import urlpatterns as reg_patterns
from .views import LimitedRegistrationView, PreRegistrationCheckView, ChooseDepartmentView, VerifyAssociationRequest

urlpatterns = patterns('',
                       url(r'^registration-check/$',
                           PreRegistrationCheckView.as_view(),
                           name='registration_preregister'),
                       url(r'^register/$',
                           LimitedRegistrationView.as_view(),
                           name='registration_register'),
                       url(r'^choose-department/$',
                           ChooseDepartmentView.as_view(),
                           name='registration_choose_department'),
                       url(r'^verify-association-request/$',
                           VerifyAssociationRequest.as_view(),
                           name='verify-association-request'),)

urlpatterns += reg_patterns
