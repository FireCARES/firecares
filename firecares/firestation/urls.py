from .views import DepartmentDetailView, Stats, FireDepartmentListView
from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page


urlpatterns = patterns('',
                       url(r'departments/(?P<pk>\d+)/?$', cache_page(60*15)(DepartmentDetailView.as_view(template_name='firestation/department_detail.html')), name='firedepartment_detail'),
                       url(r'departments/(?P<pk>\d+)/(?P<slug>[-\w]+)/?$', cache_page(60*15)(DepartmentDetailView.as_view(template_name='firestation/department_detail.html')), name='firedepartment_detail_slug'),
                       url(r'departments/?$', FireDepartmentListView.as_view(template_name='firestation/firedepartment_list.html'), name='firedepartment_list'),
                       url(r'stats/fire-stations/?$', Stats.as_view(), name='firestation_stats'),
                       )

