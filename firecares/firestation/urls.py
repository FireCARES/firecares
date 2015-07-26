from .views import FireStationDetailView, DepartmentDetailView, Stats, FireDepartmentListView, Home
from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'stations/(?P<pk>\d+)/?$', FireStationDetailView.as_view(), name='firestation_detail'),
                       url(r'departments/(?P<pk>\d+)/?$', DepartmentDetailView.as_view(template_name='firestation/department_detail.html'), name='firedepartment_detail'),
                       url(r'departments/?$', FireDepartmentListView.as_view(template_name='firestation/firedepartment_list.html'), name='firedepartment_list'),
                       url(r'departments/(?P<state>\w+)/?$', FireDepartmentListView.as_view(), name='firedepartment_list'),
                       url(r'(?P<pk>\d+)/?$', DepartmentDetailView.as_view(), name='jurisdiction_detail'),
                       url(r'stats/fire-stations/?$', Stats.as_view(), name='firestation_stats'),
                       )

