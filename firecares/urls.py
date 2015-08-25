from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.decorators.cache import cache_page
from .firestation.views import Home
from .firestation.api import StaffingResource, FireStationResource
from tastypie.api import Api
from firestation.views import Home

admin.autodiscover()
v1_api = Api(api_name='v1')
v1_api.register(StaffingResource())
v1_api.register(FireStationResource())


urlpatterns = patterns('',
    # Examples:
    url(r'^$', cache_page(60*15)(Home.as_view()), name='firestation_home'),
    url(r'^', include('firecares.firestation.urls')),
    (r'^api/', include(v1_api.urls)),
    (r'^accounts/', include('registration.backends.default.urls')),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login', kwargs={'template_name': 'accounts/login.html'}),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^autocomplete/', include('autocomplete_light.urls')),
)
