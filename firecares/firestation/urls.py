from .views import DepartmentDetailView, Stats, FireStationListView, SuggestedDepartmentsView, FireDepartmentListView
from django.conf.urls import patterns, url


urlpatterns = patterns('',
                       url(r'departments/(?P<pk>\d+)/?$', DepartmentDetailView.as_view(template_name='firestation/department_detail.html'), name='firedepartment_detail'),
                       url(r'departments/(?P<pk>\d+)/(?P<slug>[-\w]+)/?$', DepartmentDetailView.as_view(template_name='firestation/department_detail.html'), name='firedepartment_detail_slug'),
                       url(r'departments/?$', FireDepartmentListView.as_view(template_name='firestation/firedepartment_list.html'), name='firedepartment_list'),
                       url(r'stats/fire-stations/?$', Stats.as_view(), name='firestation_stats'),
                       url(r'stations/?$', FireStationListView.as_view(template_name='firestation/firestation_list.html'), name='firestation_list'),
                       url(r'stations/(?P<pk>\d+)/suggested$', SuggestedDepartmentsView.as_view(template_name='firestation/suggested_departments.html'), name='suggested_departments'),
                       )

