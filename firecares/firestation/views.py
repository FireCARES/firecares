import json
import logging
import math
import ogr
import os
import osr
import shutil
import urllib
import uuid
from django.utils import timezone
from django.views.generic import DetailView, ListView, TemplateView, View, CreateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http.response import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db import connection, transaction
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist
from django.db.utils import ProgrammingError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http.response import HttpResponseBadRequest
from django.template import loader
from django.utils.encoding import smart_str
from firecares.tasks.email import send_mail
from firecares.utils import get_property
from firecares.firecares_core.ext.invitations.views import send_invites
from firecares.firecares_core.mixins import LoginRequiredMixin
from firecares.firecares_core.models import RegistrationWhitelist, AccountRequest
from firecares.usgs.models import (StateorTerritoryHigh, CountyorEquivalent,
                                   Reserve, NativeAmericanArea, IncorporatedPlace,
                                   UnincorporatedPlace, MinorCivilDivision)
from guardian.mixins import PermissionRequiredMixin
from tempfile import mkdtemp
from firecares.tasks.cleanup import remove_file
from .forms import DocumentUploadForm, DepartmentUserApprovalForm, DataFeedbackForm, AddStationForm
from django.views.generic.edit import FormView
from .models import (Document, FireStation, FireDepartment, Staffing)
from favit.models import Favorite
from invitations.models import Invitation

User = get_user_model()
log = logging.getLogger(__name__)


class FeaturedDepartmentsMixin(object):
    """
    Mixin to add featured departments to a request.
    """

    @staticmethod
    def get_featured_departments():
        return FireDepartment.priority_departments.all()


class PaginationMixin(object):

    def get_context_data(self, **kwargs):
        context = super(PaginationMixin, self).get_context_data(**kwargs)
        paginator = context['paginator']
        page_obj = context['page_obj']
        return PaginationMixin.populate_context_data(context, paginator, page_obj.number)

    @staticmethod
    def populate_context_data(context, paginator, page_number):
        min_page = max(1, page_number - 2)
        max_page = min(paginator.num_pages, min_page + 4)
        context['windowed_range'] = range(min_page, max_page + 1)
        if min_page > 1:
            context['first_page'] = 1
        if max_page < paginator.num_pages:
            context['last_page'] = paginator.num_pages
        return context


class DepartmentDetailView(DetailView):
    model = FireDepartment
    template_name = 'firestation/department_detail.html'
    objects_per_page = 10

    def get_context_data(self, **kwargs):
        context = super(DepartmentDetailView, self).get_context_data(**kwargs)
        fd = context['object']

        context['user_can_change'] = self.request.user.is_authenticated() and\
            fd.is_curator(self.request.user)
        context['user_can_admin'] = self.request.user.is_authenticated() and\
            fd.is_admin(self.request.user)

        page = self.request.GET.get('page')
        paginator = Paginator(context['firedepartment'].firestation_set.filter(archived=False).order_by('station_number'), self.objects_per_page)

        try:
            stations = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            stations = paginator.page(1)
            page = 1
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            stations = paginator.page(paginator.num_pages)
            page = paginator.num_pages

        context['firestations'] = stations
        context['page_obj'] = stations

        if not page:
            page = 1
        PaginationMixin.populate_context_data(context, paginator, int(page))

        # population stats provide summary statistics for fields within the current objects population class
        context['population_stats'] = self.object.metrics.population_class_stats

        return context


class AdminDepartmentUsers(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = FireDepartment
    template_name = 'firestation/department_admin_users.html'
    permission_required = 'admin_firedepartment'

    def get_context_data(self, **kwargs):
        context = super(AdminDepartmentUsers, self).get_context_data(**kwargs)
        users = sorted(self.object.get_users_with_permissions(), key=lambda x: x.username)
        user_perms = []
        fd = self.object
        for u in users:
            user_perms.append(dict(user=u,
                                   can_change=fd.is_curator(u),
                                   can_admin=fd.is_admin(u)))
        context['user_perms'] = user_perms
        context['user_can_change'] = fd.is_curator(self.request.user)
        context['user_can_admin'] = fd.is_admin(self.request.user)
        context['invites'] = Invitation.objects.filter(departmentinvitation__department=self.object).order_by('-sent')
        context['whitelists'] = [dict(id=w.id,
                                      email_or_domain=w.email_or_domain,
                                      is_domain_whitelist=w.is_domain_whitelist,
                                      give_curator='change_firedepartment' in (w.permission or ''),
                                      give_admin='admin_firedepartment' in (w.permission or ''))
                                 for w in RegistrationWhitelist.for_department(self.object)]
        return context

    def post(self, request, **kwargs):
        self.object = self.get_object()
        section = request.POST.get('form')

        if section == 'whitelist':
            items = zip(request.POST.getlist('id'),
                        request.POST.getlist('email_or_domain'),
                        request.POST.getlist('give_curator'),
                        request.POST.getlist('give_admin'))

            # Delete any whitelist items that don't come back
            RegistrationWhitelist.for_department(self.object).exclude(id__in=[int(i[0]) for i in items if i[0]]).delete()

            # Create new items
            for i in filter(lambda x: x[0] == '', items):
                give_curator = 'change_firedepartment' if i[2] == 'true' else ''
                give_admin = 'admin_firedepartment' if i[3] == 'true' else ''
                reg = RegistrationWhitelist.objects.create(department=self.object,
                                                           email_or_domain=i[1],
                                                           created_by=request.user,
                                                           permission=','.join([give_curator, give_admin]))
                # Also, send email IF it's an individual email address that is being whitelisted
                if not reg.is_domain_whitelist:
                    context = dict(whitelist=reg, site=get_current_site(request))
                    body = loader.render_to_string('registration/email_has_been_whitelisted.txt', context)
                    subject = 'Your email address is allowed to login to or register with FireCARES'
                    email_message = EmailMultiAlternatives(
                        subject,
                        body,
                        settings.DEFAULT_FROM_EMAIL,
                        [reg.email_or_domain],
                        reply_to=['contact@firecares.org'])
                    send_mail.delay(email_message)

            messages.add_message(request, messages.SUCCESS, 'Updated whitelisted registration emails addresses/domains for this department in FireCARES.')
        elif section == 'users':
            users = self.object.get_users_with_permissions()

            can_admin_users = request.POST.getlist('can_admin')
            can_change_users = request.POST.getlist('can_change')
            skipped = set([])

            for user in can_admin_users:
                cur = User.objects.filter(email=user).first()
                if not cur:
                    skipped.add(user)
                    continue
                self.object.add_admin(cur)
            for user in users:
                if user.email not in can_admin_users:
                    self.object.remove_admin(user)

            for user in can_change_users:
                cur = User.objects.filter(email=user).first()
                if not cur:
                    skipped.add(user)
                    continue
                self.object.add_curator(cur)
            for user in users:
                if user.email not in can_change_users:
                    self.object.remove_curator(user)

            if skipped:
                messages.add_message(request, messages.ERROR, 'Unable to find users with email addresses, skipping: {}'.format(', '.join(skipped)))

            messages.add_message(request, messages.SUCCESS, 'Updated department\'s authorized users.')
        else:
            return HttpResponseBadRequest()
        return redirect(self.object)


class DepartmentUpdateGovernmentUnits(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    """
    View to update a Department's associated government units.
    """
    model = FireDepartment
    template_name = 'firestation/department_update_government_units.html'
    permission_required = 'change_firedepartment'

    def _associated_government_unit_ids(self, model_type):
        return self.object.government_unit.filter(object_type=ContentType.objects.get_for_model(model_type)).values_list('object_id', flat=True)

    def get_context_data(self, **kwargs):
        context = super(DepartmentUpdateGovernmentUnits, self).get_context_data(**kwargs)

        og = self.object.headquarters_geom.clone()
        # 5km-ish
        geom = og.buffer(5000 / 40000000. * 360. / math.cos(og.y / 360. * math.pi))

        context['user_can_change'] = self.object.is_curator(self.request.user)
        context['user_can_admin'] = self.object.is_admin(self.request.user)

        context['current_incorporated_places'] = self._associated_government_unit_ids(IncorporatedPlace)
        context['incorporated_places'] = IncorporatedPlace.objects.filter(geom__intersects=geom)
        context['current_minor_civil_divisions'] = self._associated_government_unit_ids(MinorCivilDivision)
        context['minor_civil_divisions'] = MinorCivilDivision.objects.filter(geom__intersects=geom)
        context['current_native_american_areas'] = self._associated_government_unit_ids(NativeAmericanArea)
        context['native_american_areas'] = NativeAmericanArea.objects.filter(geom__intersects=geom)
        context['current_reserves'] = self._associated_government_unit_ids(Reserve)
        context['reserves'] = Reserve.objects.filter(geom__intersects=geom)
        context['current_unincorporated_places'] = self._associated_government_unit_ids(UnincorporatedPlace)
        context['unincorporated_places'] = UnincorporatedPlace.objects.filter(geom__intersects=geom)
        context['current_counties'] = self._associated_government_unit_ids(CountyorEquivalent)
        context['counties'] = CountyorEquivalent.objects.filter(geom__intersects=geom)

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()

        incorporated_places_selections = map(int, request.POST.getlist('incorporated_places'))
        minor_civil_divisions_selections = map(int, request.POST.getlist('minor_civil_divisions'))
        native_american_areas_selections = map(int, request.POST.getlist('native_american_areas'))
        reserves_selections = map(int, request.POST.getlist('reserves'))
        unincorporated_places_selections = map(int, request.POST.getlist('unincorporated_places'))
        counties_selections = map(int, request.POST.getlist('counties'))

        def _update_govt_units(selections, current, model_type):
            for i in set(selections) | set(current):
                if i in selections and i not in current:
                    self.object.government_unit.connect(model_type.objects.get(pk=i))
                elif i not in selections and i in current:
                    self.object.government_unit.filter(object_id=i, object_type=ContentType.objects.get_for_model(model_type)).delete()

        _update_govt_units(counties_selections, context['current_counties'], CountyorEquivalent)
        _update_govt_units(unincorporated_places_selections, context['current_unincorporated_places'], UnincorporatedPlace)
        _update_govt_units(reserves_selections, context['current_reserves'], Reserve)
        _update_govt_units(native_american_areas_selections, context['current_native_american_areas'], NativeAmericanArea)
        _update_govt_units(minor_civil_divisions_selections, context['current_minor_civil_divisions'], MinorCivilDivision)
        _update_govt_units(incorporated_places_selections, context['current_incorporated_places'], IncorporatedPlace)

        if request.POST.get('update_geom'):
            self.object.set_geometry_from_government_unit()
            self.object.set_population_from_government_unit()

        messages.add_message(request, messages.SUCCESS, 'Government unit associations updated')

        self.object.save()

        return redirect(self.object)


class DepartmentDataValidationView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    """
    View to update a Department's associated government units.
    """
    model = FireDepartment
    template_name = 'firestation/department_data_validation.html'
    permission_required = 'change_firedepartment'

    def get_context_data(self, **kwargs):
        department = get_object_or_404(FireDepartment, pk=self.kwargs.get('pk'))

        context = super(DepartmentDataValidationView, self).get_context_data(**kwargs)
        context['object'] = department

        context['user_can_change'] = self.object.is_curator(self.request.user)
        context['user_can_admin'] = self.object.is_admin(self.request.user)

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        self.object.staffing_verified = map(bool, request.POST.getlist('staffing'))
        self.object.stations_verified = map(bool, request.POST.getlist('stations'))
        self.object.boundary_verified = map(bool, request.POST.getlist('boundary'))

        messages.add_message(request, messages.SUCCESS, 'Department Data Validation updated')

        self.object.save()

        return redirect(self.object)


class RemoveIntersectingDepartments(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    """
    View to update a Department's government unit.
    """
    model = FireDepartment
    template_name = 'firestation/department_remove_intersecting_departments.html'
    permission_required = 'change_firedepartment'

    def get_context_data(self, **kwargs):
        context = super(RemoveIntersectingDepartments, self).get_context_data(**kwargs)

        context['user_can_change'] = self.object.is_curator(self.request.user)
        context['user_can_admin'] = self.object.is_admin(self.request.user)

        context['intersecting_departments'] = self.get_intersecting_departments()

        return context

    def get_intersecting_departments(self):
        return FireDepartment.objects \
            .filter(geom__intersects=self.object.geom) \
            .exclude(id=self.object.id) \
            .exclude(id__in=self.object.intersecting_department.all().values_list('removed_department_id', flat=True))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        departments = map(int, request.POST.getlist('departments'))

        # Make sure POSTed departments are still intersecting.
        for i in set(departments).intersection(set(self.get_intersecting_departments().values_list('id', flat=True))):
            self.object.remove_from_department(FireDepartment.objects.get(id=i))

        self.object.save()

        messages.add_message(request, messages.SUCCESS, 'Removed intersecting departments.')

        return redirect(self.object)


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
                queryset = queryset.extra(select={'population_is_null': 'population IS NULL'}) \
                    .order_by('population_is_null', '-population')

        # default sorting to -population and put null values at the end.
        else:
            queryset = queryset.extra(select={'population_is_null': 'population IS NULL'}) \
                .order_by('population_is_null', '-population')

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

            # make sure the limit is not 0
            if limit:
                self.paginate_by = limit

        except Exception:
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


class FireDepartmentListView(PaginationMixin, ListView, SafeSortMixin, LimitMixin,
                             FeaturedDepartmentsMixin):
    model = FireDepartment
    paginate_by = 30
    queryset = FireDepartment.objects.filter(archived=False)
    sort_by_fields = [
        ('name', 'Name Ascending'),
        ('-name', 'Name Descending'),
        ('state', 'State Acscending'),
        ('-state', 'State Descending'),
        ('dist_model_score', 'Lowest Performance Score'),
        ('-dist_model_score', 'Highest Performance Score'),
        ('population', 'Smallest Population'),
        ('-population', 'Largest Population')
    ]

    search_fields = ['fdid', 'state', 'region', 'name']
    range_fields = ['population', 'dist_model_score']

    def handle_search(self, queryset):

        # search in favorite departments only
        if self.request.GET.get('favorites', 'false') == 'true' and self.request.user.is_authenticated():
            favorite_departments = map(lambda obj: obj.target.pk,
                                       Favorite.objects.for_user(self.request.user, model=FireDepartment))
            queryset = queryset.filter(pk__in=favorite_departments)

        # If there is a 'q' argument, this is a full text search.
        if self.request.GET.get('q'):
            queryset = queryset.full_text_search(self.request.GET.get('q'))

        if self.request.GET.get('weather', 'false') == 'true':
            queryset = queryset.filter(**{'departmentwarnings__expiredate__gte': timezone.now()}).distinct()

        if self.request.GET.get('cfai', 'false') == 'true':
            queryset = queryset.filter(**{'cfai_accredited': True})

        queryset = self.sort_queryset(queryset, self.request.GET.get('sortBy'))
        self.limit_queryset(self.request.GET.get('limit'))

        for field, value in self.request.GET.items():
            if value and value.lower() != 'any' and field in self.search_fields:
                if field.lower().endswith('name'):
                    field += '__icontains'
                queryset = queryset.filter(**{field: value})

            # range is passed as pair of comma delimited min and max values for example 12,36
            try:
                if field in self.range_fields and value and "," in value:
                    min, max = value.split(",")
                    Min = int(min)
                    Max = int(max)

                    if field == 'dist_model_score':
                        # include null values with a zero query
                        from django.db.models import Q
                        # don't filter and show all, some data has no level
                        if Max < 380:
                            queryset = queryset.filter(Q(**{'firedepartmentriskmodels__level': 0, 'firedepartmentriskmodels__dist_model_score__lte': Max}) | Q(**{'firedepartmentriskmodels__level': 0, 'firedepartmentriskmodels__dist_model_score__isnull': True}))

                        if str(Min) != '0':
                            queryset = queryset.filter(**{'firedepartmentriskmodels__level': 0, 'firedepartmentriskmodels__dist_model_score__gte': Min})
                    else:
                        if Min:
                            queryset = queryset.filter(**{field + '__gte': Min})

                        if Max:
                            from django.db.models import Q
                            queryset = queryset.filter(Q(**{field + '__lte': Max}) | Q(**{field + '__isnull': True}))

            except Exception:
                pass
        return queryset

    def get_queryset(self):
        queryset = super(FireDepartmentListView, self).get_queryset()
        queryset = self.handle_search(queryset)

        try:
            with transaction.atomic():
                queryset.count()
        except ProgrammingError as e:
            log.warning(e)
            queryset = super(FireDepartmentListView, self).get_queryset()

        return queryset

    def get_context_data(self, **kwargs):
        context = super(FireDepartmentListView, self).get_context_data(**kwargs)
        context = self.get_sort_context(context)
        featured_departments = self.get_featured_departments().order_by('?')
        context['featured_departments'] = featured_departments[:5]
        context['featured_departments_short'] = featured_departments[:3]

        context['departments_total_count'] = self.get_queryset().count()

        context['dist_min'] = 0

        return context


class SimilarDepartmentsListView(FireDepartmentListView):
    """
    Implements the Similar Department list view.
    """

    def get_queryset(self):
        department = get_object_or_404(FireDepartment, pk=self.kwargs.get('pk'))
        queryset = department.similar_departments
        queryset = self.handle_search(queryset)
        return queryset


class AddStationView(LoginRequiredMixin, FormView):
    """
    Implements the Add Station View
    """
    template_name = 'firestation/firestation_add.html'
    station = 0
    form_class = AddStationForm
    address_string = ""

    def get_context_data(self, **kwargs):
        department = get_object_or_404(FireDepartment, pk=self.kwargs.get('pk'))

        context = super(AddStationView, self).get_context_data(**kwargs)
        context['object'] = department

        return context

    def post(self, request, *args, **kwargs):
        form = AddStationForm(department_pk=self.kwargs.get('pk'), **self.get_form_kwargs())
        if request.method == 'POST':
            if form.is_valid():
                fd = FireDepartment.objects.get(pk=self.kwargs.get('pk'))
                # Check that name is not used already
                duplicate_station = FireStation.objects.filter(name=form.cleaned_data['name'], department=fd)
                if duplicate_station.exists():
                    messages.add_message(request, messages.ERROR, 'The name submitted is already in use.')
                    return super(AddStationView, self).form_invalid(form)
                # Check that station id is not used already
                duplicate_id = FireStation.objects.filter(station_number=form.cleaned_data['station_number'], department=fd)
                if duplicate_id.exists():
                    messages.add_message(request, messages.ERROR, 'The station number submitted is already in use.')
                    return super(AddStationView, self).form_invalid(form)
                self.address_string = request.POST.get('hidaddress', '')
                if self.form_valid(form) == 'Geocode Error':
                    messages.add_message(request, messages.ERROR, 'A geocoding error has occured finding the Station location.  Please check the address or try again in a few minutes.')
                    return super(AddStationView, self).form_invalid(form)
                else:
                    messages.success(request, 'Station Created successfully')
                    return super(AddStationView, self).form_valid(form)
            else:
                messages.add_message(request, messages.ERROR, 'The address submitted is not valid.  Please try again.')
                return self.form_invalid(form)

    def form_valid(self, form):
        try:
            station = form.save(commit=False)
            fd = FireDepartment.objects.get(pk=self.kwargs.get('pk'))
            address_string = self.address_string
            station = station.create_station(department=fd, address_string=address_string, name=station.name, station_number=station.station_number)
            if station is None:
                return "Geocode Error"
            else:
                self.station = station
                return super(AddStationView, self).form_valid(form)

        except Exception:
            print('Geocoding Problem')
            return "Geocode Error"

    def get_success_url(self):
        return reverse('firestation_detail_slug', kwargs=dict(pk=self.station.id, slug=self.station.slug))


class FireStationFavoriteListView(LoginRequiredMixin, PaginationMixin, ListView, SafeSortMixin, LimitMixin):
    """
    Implements the Favorite Station list view.
    """

    model = FireStation
    paginate_by = 15
    sort_by_fields = [
        ('name', 'Name Ascending'),
        ('-name', 'Name Descending')
    ]

    def get_queryset(self):
        favorites = Favorite.objects.for_user(self.request.user, model=FireStation)
        favorite_station_pk = map(lambda obj: obj.target.pk, favorites)
        queryset = FireStation.objects.all().filter(pk__in=favorite_station_pk)

        order_by = self.request.GET.get('sortBy')
        if self.model_field_valid(order_by, choices=[name for name, verbose_name in self.sort_by_fields]):
            queryset = queryset.order_by(order_by)

        self.limit_queryset(self.request.GET.get('limit'))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(FireStationFavoriteListView, self).get_context_data(**kwargs)
        context = self.get_sort_context(context)

        paginator = context['paginator']
        page_obj = context['page_obj']
        try:
            stations = paginator.page(page_obj.number)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            stations = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            stations = paginator.page(paginator.num_pages)
        context['firestations'] = stations
        context['firestations_total_count'] = len(self.get_queryset())
        return context


class FireStationDetailView(LoginRequiredMixin, DetailView):
    model = FireStation

    def get_context_data(self, **kwargs):
        context = super(FireStationDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        fd = context['object'].department
        has_fd = bool(fd)
        can_change = user.is_authenticated() and ((has_fd and fd.is_curator(user)) or user.is_superuser)
        can_admin = user.is_authenticated() and ((has_fd and fd.is_admin(user)) or user.is_superuser)
        context['user_can_change'] = can_change
        context['user_can_admin'] = can_admin
        return context


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
            fd = FireDepartment.objects.create(
                name='{0} {1} Fire Department'.format(county.county_name, county.get_fcode_display()),
                content_object=county,
                geom=county.geom)
            fd.save()
            FireStation.objects.filter(geom__intersects=county.geom).update(department=fd)
            return HttpResponseRedirect(reverse('set_fire_district', args=[county.id]))


class Stats(LoginRequiredMixin, TemplateView):
    template_name = 'firestation/firestation_stats.html'

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


class DownloadShapefile(LoginRequiredMixin, View):
    content_type = 'application/zip'
    output_dir = '/tmp'

    def get_queryset(self, *args, **kwargs):
        if kwargs.get('feature_type') == 'department_boundary':
            return FireDepartment.objects.filter(id=kwargs.get('pk'))
        elif kwargs.get('feature_type') == 'firestation_boundary':
            return FireStation.objects.filter(id=kwargs.get('pk'))
        else:
            return kwargs.get('instance').firestation_set.all()

    def create_shapefile(self, queryset, filename, geom):
        path = mkdtemp()
        file_path = os.path.join(path, filename)
        geom_type = ogr.wkbPoint

        if queryset.model._meta.get_field_by_name(geom)[0].geom_type == 'MULTIPOLYGON':
            geom_type = ogr.wkbMultiPolygon

        driver = ogr.GetDriverByName("ESRI Shapefile")

        # create the data source
        data_source = driver.CreateDataSource(file_path)

        # create the spatial reference, WGS84
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        # create the layer
        layer = data_source.CreateLayer(filename, srs, geom_type)

        # Name, Type, Width
        fields = [
            ('id', ogr.OFTInteger, None),
            ('station_id', ogr.OFTInteger, None),
            ('name', ogr.OFTString, 254),
            ('department', ogr.OFTInteger, None),
            ('station_nu', ogr.OFTInteger, None),
            ('address_l1', ogr.OFTString, 100),
            ('address_l2', ogr.OFTString, 100),
            ('city', ogr.OFTString, 50),
            ('state', ogr.OFTString, 40),
            ('zipcode', ogr.OFTString, 10),
            ('country', ogr.OFTString, 2),
        ]

        ids = queryset.values_list('id', flat=True)

        # Pivot staffing rows per apparatus without aggregating
        # resulting in multiple columns if a station has more than one of any apparatus type
        for apparatus, apparatus_alias in Staffing.APPARATUS_SHAPEFILE_CHOICES:

            cursor = connection.cursor()
            sql = "select count(*) from firestation_staffing  where firestation_id in %s and apparatus=%s " \
                  "group by firestation_id order by count(*) desc limit 1;"
            cursor.execute(sql, [tuple(ids), apparatus])
            row = cursor.fetchone()
            count = 0

            if row:
                count = row[0]

            for n in range(0, count) or [0]:
                field_name = apparatus_alias

                if n > 0:
                    field_name = apparatus_alias + '_{0}'.format(n)

                fields.append((field_name, ogr.OFTInteger, None))

        for alias, field_type, width in fields:
            field = ogr.FieldDefn(alias, field_type)

            if width:
                field.SetWidth(width)

            layer.CreateField(field)
            field = None

        # Process the text file and add the attributes and features to the shapefile
        for row in queryset:

            raw_geom = getattr(row, geom)
            wkt = None

            if raw_geom:
                wkt = raw_geom.wkt
            else:
                continue

            feature = ogr.Feature(layer.GetLayerDefn())

            # Set the attributes using the values from the delimited text file

            field_mappings = {
                'name': 'name',
                'station_nu': 'station_number',
                'department': 'department.id',
                'station_nu': 'station_number',
                'address_l1': 'station_address.address_line1',
                'address_l2': 'station_address.address_line2',
                'country': 'station_address.country_id',
                'state': 'station_address.state_province',
                'city': 'station_address.city',
                'zipcode': 'station_address.postal_code',
                'station_id': 'id',
            }

            for field, obj_prop in field_mappings.items():
                value = get_property(row, obj_prop)
                if value:
                    if isinstance(value, basestring):
                        feature.SetField(field, str(value))
                    else:
                        feature.SetField(field, value)

            # Populate staffing for each unit
            for apparatus, apparatus_alias in Staffing.APPARATUS_SHAPEFILE_CHOICES:

                for n, record in enumerate(row.staffing_set.filter(apparatus=apparatus)):
                    apparatus_alias_index = apparatus_alias

                    if n > 0:
                        apparatus_alias_index += '_{0}'.format(n)

                    feature.SetField(apparatus_alias_index, record.personnel)

            # Create the point from the Well Known Txt
            point = ogr.CreateGeometryFromWkt(wkt)

            # Set the feature geometry using the point
            feature.SetGeometry(point)
            # Create the feature in the layer (shapefile)
            layer.CreateFeature(feature)
            # Destroy the feature to free resources
            feature.Destroy()

        # Destroy the data source to free resources
        data_source.Destroy()

        if os.path.exists(os.path.join(self.output_dir, filename + '.zip')):
            filename += '-' + str(uuid.uuid4())[:5]

        zip_file = shutil.make_archive(self.output_dir + '/' + filename, 'zip', file_path)

        if self.request.META.get('SERVER_NAME') != 'testserver':
            remove_file.delay(path)
            remove_file.delay(zip_file, countdown=600)

        return file_path, zip_file

    def create_department_boundary_shapefile(self, queryset, filename, geom):
        path = mkdtemp()
        file_path = os.path.join(path, filename)
        geom_type = ogr.wkbPoint

        if queryset.model._meta.get_field_by_name(geom)[0].geom_type == 'MULTIPOLYGON':
            geom_type = ogr.wkbMultiPolygon

        driver = ogr.GetDriverByName("ESRI Shapefile")

        # create the data source
        data_source = driver.CreateDataSource(file_path)

        # create the spatial reference, WGS84
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        # create the layer
        layer = data_source.CreateLayer(filename, srs, geom_type)
        for row in queryset:
            raw_geom = getattr(row, geom)
            wkt = None

            if raw_geom:
                wkt = raw_geom.wkt
            else:
                continue

            feature = ogr.Feature(layer.GetLayerDefn())
            point = ogr.CreateGeometryFromWkt(wkt)

            # Set the feature geometry using the point
            feature.SetGeometry(point)
            layer.CreateFeature(feature)
            feature.Destroy()

        data_source.Destroy()

        if os.path.exists(os.path.join(self.output_dir, filename + '.zip')):
            filename += '-' + str(uuid.uuid4())[:5]

        zip_file = shutil.make_archive(self.output_dir + '/' + filename, 'zip', file_path)

        if self.request.META.get('SERVER_NAME') != 'testserver':
            remove_file.delay(path)
            remove_file.delay(zip_file, countdown=600)

        return file_path, zip_file

    def filename(self, *args, **kwargs):
        return '{0}-{1}-{2}'.format(kwargs.get('instance').id,
                                    kwargs.get('instance').slug,
                                    kwargs.get('geom_type'))

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type=self.content_type)
        geom = self.kwargs.get('geometry_field', 'geom')
        feature_type = kwargs.get('feature_type')

        geom_type = self.kwargs.get('geom_type', 'stations')

        if geom == 'district':
            if feature_type == 'firestation_boundary':
                geom_type = 'district'
            else:
                geom_type = 'districts'

        if feature_type == 'firestation_boundary':
            instance = get_object_or_404(FireStation, id=kwargs['pk'])
        else:
            instance = get_object_or_404(FireDepartment, id=kwargs['pk'])

        filename = self.filename(instance=instance, geom_type=geom_type)
        queryset = self.get_queryset(instance=instance, **kwargs)

        if kwargs.get('feature_type') == 'department_boundary':
            file_path, zip_file = self.create_department_boundary_shapefile(queryset, filename, geom)
        else:
            file_path, zip_file = self.create_shapefile(queryset, filename, geom)
        response['Content-Disposition'] = 'attachment; filename="{0}.zip"'.format(smart_str(filename))
        response['X-Accel-Redirect'] = smart_str(zip_file)
        response.content = file_path
        return response


class DocumentsView(LoginRequiredMixin, FormView):
    template_name = 'firestation/department_documents.html'
    success_url = 'documents'
    form_class = DocumentUploadForm
    objects_per_page = 25

    def get_context_data(self, **kwargs):
        context = super(DocumentsView, self).get_context_data(**kwargs)

        department = get_object_or_404(FireDepartment, pk=self.kwargs.get('pk'))
        document_list = department.document_set.all().order_by('-created')

        paginator = Paginator(document_list, self.objects_per_page)
        page = self.request.GET.get('page')

        try:
            documents = paginator.page(page)
        except PageNotAnInteger:
            documents = paginator.page(1)
        except EmptyPage:
            documents = paginator.page(paginator.num_pages)

        context['documents'] = documents
        context['object'] = department

        context['user_can_change'] = department.is_curator(self.request.user)
        context['user_can_admin'] = department.is_admin(self.request.user)

        return context

    def post(self, request, *args, **kwargs):
        department = get_object_or_404(FireDepartment, pk=self.kwargs.get('pk'))
        if department.is_curator(self.request.user):
            form = DocumentUploadForm(department_pk=self.kwargs.get('pk'), **self.get_form_kwargs())
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        else:
            return HttpResponse(status=401)

    def form_valid(self, form):
        document = form.save(commit=False)
        document.department = FireDepartment.objects.get(pk=self.kwargs.get('pk'))
        document.filename = os.path.basename(os.path.normpath(document.file.name))
        document.uploaded_by = self.request.user
        document.save()

        return super(DocumentsView, self).form_valid(form)


class DocumentsDeleteView(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = FireDepartment
    permission_required = 'change_firedepartment'

    def post(self, request, *args, **kwargs):
        document = get_object_or_404(Document,
                                     department=self.get_object(),
                                     filename=request.POST.get('filename'))
        document.file.delete()
        document.delete()
        return JsonResponse({})


class DocumentsFileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse()
        response['X-Accel-Redirect'] = '/files/%s/departments/%s/%s' % (settings.DOCUMENT_UPLOAD_BUCKET,
                                                                        kwargs.get('pk'),
                                                                        kwargs.get('filename'))
        return response


class AdminDepartmentAccountRequests(PermissionRequiredMixin, LoginRequiredMixin, DetailView):
    model = FireDepartment
    template_name = 'firestation/department_verify_user_account.html'
    permission_required = 'admin_firedepartment'

    def get_context_data(self, **kwargs):
        context = super(AdminDepartmentAccountRequests, self).get_context_data(**kwargs)
        email = self.request.GET['email']
        context['form'] = DepartmentUserApprovalForm(initial=dict(email=email))
        context['existing'] = AccountRequest.objects.filter(Q(approved_by__isnull=False) | Q(denied_by__isnull=False), email=email).first()

        context['user_can_change'] = self.object.is_curator(self.request.user)
        context['user_can_admin'] = self.object.is_admin(self.request.user)

        return context

    def get(self, request, **kwargs):
        if 'email' not in request.GET:
            return HttpResponseBadRequest('email querystring param required')

        return super(AdminDepartmentAccountRequests, self).get(request, **kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()

        form = DepartmentUserApprovalForm(self.request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            req = AccountRequest.objects.get(email=email)

            if form.cleaned_data['approved']:
                req.approve(self.request.user)
                messages.add_message(self.request, messages.SUCCESS, 'Invited {} to FireCARES.'.format(email))
                send_invites([dict(email=email, department_id=self.object.id)], self.request)
            else:
                req.deny(self.request.user)
                messages.add_message(self.request, messages.SUCCESS, 'Denied {}\'s request for an account on FireCARES.'.format(email))

                body = form.cleaned_data['message']
                context = dict(account_request=req, message=body, site=get_current_site(self.request))
                body = loader.render_to_string('registration/department_account_request_email.txt', context)
                subject = 'Your FireCARES account request'
                email_message = EmailMultiAlternatives(subject, body, settings.DEFAULT_FROM_EMAIL, [req.email])
                send_mail.delay(email_message)

        return redirect(self.object)


class DataFeedbackView(LoginRequiredMixin, CreateView):
    """
    Processes data feedback
    """
    form_class = DataFeedbackForm
    http_method_names = ['post']

    def _send_email(self):
        """
        Email admins when new feedback are received
        """
        to = [x[1] for x in settings.DATA_FEEDBACK_EMAILS]
        body = loader.render_to_string('contact/data_feedback.txt', dict(contact=self.object))
        email_message = EmailMultiAlternatives('{} - New feedback received.'.format(Site.objects.get_current().name),
                                               body,
                                               settings.DEFAULT_FROM_EMAIL,
                                               to,
                                               reply_to=[self.object.user.email])
        send_mail.delay(email_message)

    def _save_and_notify(self, form):
        self.object = form.save()
        self._send_email()
        # After success return created response
        return HttpResponse(status=201)

    def form_valid(self, form):
        """
        If the form is valid then send email with the feedback message
        """
        return self._save_and_notify(form)

    def form_invalid(self, form):
        """
        If the form is invalid, return errors as json.
        """
        return HttpResponse(
            json.dumps(form.errors),
            content_type="application/json",
            status=400
        )
        return super(DataFeedbackView, self).get_context_data()
