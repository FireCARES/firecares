from .views import DepartmentDetailView, Stats, FireDepartmentListView
from django.views.generic import TemplateView
from django.conf.urls import patterns, url
from django.views.decorators.cache import cache_page


urlpatterns = patterns('',
                       url(r'departments/(?P<pk>\d+)/?$', DepartmentDetailView.as_view(template_name='firestation/department_detail.html'), name='firedepartment_detail'),
                       url(r'departments/(?P<pk>\d+)/(?P<slug>[-\w]+)/?$', DepartmentDetailView.as_view(template_name='firestation/department_detail.html'), name='firedepartment_detail_slug'),
                       url(r'departments/?$', FireDepartmentListView.as_view(template_name='firestation/firedepartment_list.html'), name='firedepartment_list'),
                       url(r'community-risk$', cache_page(60 * 60 * 24)(TemplateView.as_view(template_name='firestation/community_risk_model.html')), name='models_community_risk'),
                       url(r'performance-score$', cache_page(60 * 60 * 24)(TemplateView.as_view(template_name='firestation/performance_score_model.html')), name='models_performance_score'),
                       url(r'stats/fire-stations/?$', Stats.as_view(), name='firestation_stats'),
                       )

