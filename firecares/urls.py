from django.conf.urls import patterns, include, url
from .firestation.views import Home

from .firestation.api import StaffingResource, FireStationResource
from tastypie.api import Api
from firestation.views import Home

#admin.autodiscover()
v1_api = Api(api_name='v1')
v1_api.register(StaffingResource())
v1_api.register(FireStationResource())


urlpatterns = patterns('',
    # Examples:
    url(r'^$', Home.as_view(), name='firestation_home'),
    url(r'^', include('firecares.firestation.urls')),
    (r'^api/', include(v1_api.urls)),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
