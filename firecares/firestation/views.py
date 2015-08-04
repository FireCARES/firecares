import json
from .models import FireStation, FireDepartment
from django.views.generic import DetailView, ListView, TemplateView
from firecares.usgs.models import StateorTerritoryHigh, CountyorEquivalent, IncorporatedPlace
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from django.db.models import Max, Min, Count
from django.db.models.fields import FieldDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from numpy import histogram
from random import randint
import urllib


class DISTScoreContextMixin(object):

    @staticmethod
    def add_dist_values_to_context():
        context = {}
        metrics = FireDepartment.objects.all().aggregate(Max('dist_model_score'), Min('dist_model_score'))
        context['dist_max'] = metrics['dist_model_score__max']
        context['dist_min'] = metrics['dist_model_score__min']

        return context


class FeaturedDepartmentsMixin(object):
    """
    Mixin to add featured departments to a request.
    """
    @staticmethod
    def get_featured_departments():
        return {'featured_departments': FireDepartment.priority_departments.all().order_by('?')[:5]}


class DepartmentDetailView(DISTScoreContextMixin, DetailView):
    model = FireDepartment
    template_name = 'firestation/department_detail.html'
    page = 1
    objects_per_page = 10


    def get_histogram(self, field, bins=400):
        hist = histogram(list(FireDepartment.objects.filter(**{'{0}__isnull'.format(field): False})
                         .values_list(field, flat=True)), bins=bins)
        return json.dumps(zip(hist[1], hist[0]), separators=(',', ':'))


    def get_context_data(self, **kwargs):
        context = super(DepartmentDetailView, self).get_context_data(**kwargs)

        page = self.request.GET.get('page')

        paginator = Paginator(context['firedepartment'].firestation_set.all(), self.objects_per_page)

        try:
            stations = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            stations = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            stations = paginator.page(paginator.num_pages)

        context['firestations'] = stations

        performance_data = cache.get('all_dist_score_model__count')
        risk_model_death = cache.get('all_risk_model_death__count')
        risk_model_injuries = cache.get('all_risk_model_injuries__count')
        risk_model_fires_room = cache.get('all_risk_model_fires_room__count')
        risk_model_fires_floor = cache.get('all_risk_model_fires_floor__count')
        risk_model_fires_structure = cache.get('all_risk_model_fires_structure__count')

        if not performance_data:
            performance_data = self.get_histogram('dist_model_score')
            cache.set('all_dist_score_model__count', performance_data, timeout=60 * 60 * 24)

        if not risk_model_death:
            risk_model_death = self.get_histogram('risk_model_deaths')
            cache.set('all_risk_model_death__count', risk_model_death, timeout=60 * 60 * 24)

        if not risk_model_injuries:
            risk_model_injuries = self.get_histogram('risk_model_injuries')
            cache.set('all_risk_model_injuries__count', risk_model_injuries, timeout=60 * 60 * 24)

        if not risk_model_fires_room:
            risk_model_fires_room = self.get_histogram('risk_model_fires_room')
            cache.set('risk_model_fires_room__count', risk_model_fires_room, timeout=60 * 60 * 24)

        if not risk_model_fires_floor:
            risk_model_fires_floor = self.get_histogram('risk_model_fires_floor')
            cache.set('risk_model_fires_floor__count', risk_model_fires_floor, timeout=60 * 60 * 24)

        if not risk_model_fires_structure:
            risk_model_fires_structure = self.get_histogram('risk_model_fires_structure')
            cache.set('risk_model_fires_structure__count', risk_model_fires_structure, timeout=60 * 60 * 24)


        context['performance_data'] = performance_data
        context['risk_deaths_data'] = risk_model_death
        context['risk_injuries_data'] = risk_model_injuries
        context['risk_model_fires_room'] = risk_model_fires_room
        context['risk_model_fires_floor'] = risk_model_fires_floor
        context['risk_model_fires_structure'] = risk_model_fires_structure


        context.update(self.add_dist_values_to_context())
        return context


class SafeSortMixin(object):
    """
    Allow queryset sorting on explicit fields.
    """
    # A list of tuples containing the order_by string and verbose name
    sort_by_fields = []

    def model_field_valid(self, field, choices=None):
        """
        Ensures a model field is valid.
        """
        if not field:
            return False

        if choices and field not in choices:
            return False

        if hasattr(self, 'model'):
            try:
                self.model._meta.get_field(field.replace('-', '', 1))
            except FieldDoesNotExist:
                return False

        return True

    def get_queryset(self):
        """
        Runs the sortqueryset method on the current queryset.
        """
        queryset = super(SafeSortMixin, self).get_queryset()
        return self.sort_queryset(queryset, self.request.GET.get('sortBy'))

    def sort_queryset(self, queryset, order_by):
        """
        Sorts a queryset based after ensuring the provided field is valid.
        """
        if self.model_field_valid(order_by, choices=[name for name, verbose_name in self.sort_by_fields]):
            queryset = queryset.order_by(order_by)

            if order_by == '-population':
                queryset = queryset.filter(population__gt=0, population__isnull=False)

        return queryset

    def get_sort_context(self, context):
        """
        Adds sorting context to the context object.
        """
        context['sort_by_fields'] = []

        for field, verbose_name in self.sort_by_fields:
            get_params = self.request.GET.copy()
            get_params['sort_by'] = field
            context['sort_by_fields'].append(dict(name=verbose_name, field=field))

        context['sort_by_fields'] = json.dumps(context['sort_by_fields'])
        return context


class LimitMixin(object):

    limit_by_amounts = [15, 30, 60, 90]

    def limit_queryset(self, limit):
        """
        Limits the queryset.
        """

        try:
            limit = int(limit)
            self.paginate_by = limit

        except:
            return

    def get_queryset(self):
        """
        Runs the sortqueryset method on the current queryset.
        """
        queryset = super(LimitMixin, self).get_queryset()
        return self.limit_queryset(queryset, self.request.GET.get('limit'))

    def get_limit_context(self, context):
        """
        Adds sorting context to the context object.
        """

        context['limit_by_amounts'] = []
        get_params = self.request.GET.copy()

        for limit in self.limit_by_amounts:
            get_params['limit'] = limit
            context['limit_by_amounts'].append((self.request.path + '?' + urllib.urlencode(get_params), limit))

        return context



class FireDepartmentListView(ListView, SafeSortMixin, LimitMixin, DISTScoreContextMixin, FeaturedDepartmentsMixin):
    model = FireDepartment
    paginate_by = 30
    queryset = FireDepartment.objects.all()
    sort_by_fields = [
        ('name', 'Name Ascending'),
        ('-name', 'Name Descending'),
        ('state', 'State Acscending'),
        ('-state', 'State Descending'),
        ('dist_model_score', 'Lowest DIST Score'),
        ('-dist_model_score', 'Highest DIST Score'),
        ('population', 'Smallest Population'),
        ('-population', 'Largest Population')
        ]

    search_fields = ['fdid', 'state', 'region', 'name']


    def get_queryset(self):
        queryset = super(FireDepartmentListView, self).get_queryset()
        queryset = self.sort_queryset(queryset, self.request.GET.get('sortBy'))
        self.limit_queryset(self.request.GET.get('limit'))

        for field, value in self.request.GET.items():
            if value and value.lower() != 'any' and field in self.search_fields:
                if field.lower().endswith('name'):
                    field += '__icontains'
                queryset = queryset.filter(**{field: value})

        return queryset

    def get_context_data(self, **kwargs):
        context = super(FireDepartmentListView, self).get_context_data(**kwargs)
        context = self.get_sort_context(context)
        context.update(self.add_dist_values_to_context())
        context.update(self.get_featured_departments())
        return context


class FireStationDetailView(DetailView):
    model = FireStation

class SpatialIntersectView(ListView):
    model = FireStation
    template_name = 'firestation/department_detail.html'
    context_object_name = 'firestations'

    def get_queryset(self):
        self.object = get_object_or_404(StateorTerritoryHigh, state_name__iexact=self.kwargs.get('state'))
        return FireStation.objects.filter(geom__intersects=self.object.geom)

    def get_context_data(self, **kwargs):
        context = super(SpatialIntersectView, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context


class SetDistrictView(DetailView):
    model = CountyorEquivalent
    template_name = 'firestation/set_department.html'

    def get_context_data(self, **kwargs):
        context = super(SetDistrictView, self).get_context_data(**kwargs)
        context['stations'] = FireStation.objects.filter(geom__intersects=self.object.geom)
        context['incorporated_places'] = IncorporatedPlace.objects.filter(geom__intersects=self.object.geom)
        next_fs = FireStation.objects.filter(department__isnull=True, state='VA').order_by('?')

        if next_fs:
            context['next'] = CountyorEquivalent.objects.filter(geom__intersects=next_fs[0].geom)[0]
        return context

    def post(self, request, *args, **kwargs):
        county = self.get_object()
        try:
            fd = FireDepartment.objects.get(content_type=ContentType.objects.get_for_model(CountyorEquivalent),
                                            object_id=county.id)
        except FireDepartment.DoesNotExist:
            fd = FireDepartment.objects.create(name='{0} {1} Fire Department'.format(county.county_name, county.get_fcode_display()), content_object=county,
                                               geom=county.geom)
            fd.save()
            FireStation.objects.filter(geom__intersects=county.geom).update(department=fd)
            return HttpResponseRedirect(reverse('set_fire_district', args=[county.id]))


class Stats(TemplateView):
    template_name='firestation/firestation_stats.html'

    def get_context_data(self, **kwargs):
        context = super(Stats, self).get_context_data(**kwargs)
        context['stations'] = FireStation.objects.all()
        context['departments'] = FireDepartment.objects.all()
        context['stations_with_fdid'] = FireStation.objects.filter(fdid__isnull=False)
        context['stations_with_departments'] = FireStation.objects.filter(department__isnull=False)
        context['departments_with_government_unit'] = FireDepartment.objects.filter(object_id__isnull=True)
        return context

class Home(TemplateView):
    template_name = 'firestation/home.html'
