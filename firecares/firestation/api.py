import re
import json
import logging
import requests
from .forms import StaffingForm
from .models import FireStation, Staffing, FireDepartment, ParcelDepartmentHazardLevel, EffectiveFireFightingForceLevel
from ..utils.tastypie_geodjango import allow_geodjango_filters
from firecares.weather.models import DepartmentWarnings
from firecares.settings.base import MAPBOX_BASE_URL, MAPBOX_ACCESS_TOKEN
from firecares.utils import to_multipolygon
from firecares.celery import task_exists
from firecares.tasks.update import update_nfirs_counts, update_all_nfirs_counts, refresh_nfirs_views
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.serializers.json import DjangoJSONEncoder
from django.conf.urls import url
from django.contrib.gis import geos
from django.http import HttpResponse
from tastypie import fields
from tastypie.authentication import SessionAuthentication, ApiKeyAuthentication, MultiAuthentication, Authentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.constants import ALL
from tastypie.contrib.gis.resources import ModelResource
from tastypie.resources import Resource
from tastypie.exceptions import Unauthorized, TastypieError
from tastypie.http import HttpGone, HttpMultipleChoices
from tastypie.serializers import Serializer
from tastypie.utils import trailing_slash
from tastypie.validation import FormValidation
from guardian.core import ObjectPermissionChecker
from django.utils import timezone

logger = logging.getLogger(__name__)


# Note this is from one of my other projects, not sure it is actually needed or not.
class SessionAuth(SessionAuthentication):
    """
    This is a hack to fix a bug which returns occasional TypeErrors returned from SessionAuthentication.

    About:
    Every now and then the super class' get_identifier returns a TypeError (getattr(): attribute name must be string).
    It seems that the logic that returns the string used for the username sometimes returns None.

    """
    def get_identifier(self, request):
        """
        Provides a unique string identifier for the requestor.

        This implementation returns the user's username.
        """
        try:
            return super(SessionAuth, self).get_identifier(request)
        except TypeError:
            return getattr(request.user, 'username')


class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=DjangoJSONEncoder,
                          sort_keys=True, ensure_ascii=False, indent=self.json_indent)


class JSONDefaultModelResourceMixin(object):
    def determine_format(self, request):
        return 'application/json' if not request.GET.get('format') else super(JSONDefaultModelResourceMixin, self).determine_format(request)


class PropertyResolutionFailedException(TastypieError):
    def __init__(self, property_path, class_name, *args, **kwargs):
        msg = '"{}" does not resolve for class type {}'.format(property_path, class_name)
        super(PropertyResolutionFailedException, self).__init__(msg, *args, **kwargs)


# Pulled/modified from https://gist.github.com/7wonders/6557760
class GuardianAuthorization(DjangoAuthorization):
    """
    :create_permission_code:
        the permission code that signifies the user can create one of these objects
    :view_permission_code:
        the permission code that signifies the user can view the detail
    :update_permission_code:
        the permission code that signifies the user can update one of these objects
    :remove_permission_code:
        the permission code that signifies the user can remove one of these objects
    :kwargs:
        other permission codes
        class Something(models.Model):
            name = models.CharField()
        class SomethingResource(ModelResource):
            class Meta:
                queryset = Something.objects.all()
                authorization = GuardianAuthorization(
                    delegate_to_property = None,  # property path (dot notation) to delegate authorization to
                    view_permission_code = 'can_view',  # empty view_permission_code allows anonymous users to view
                    create_permission_code = 'can_create',
                    update_permission_code = 'can_update',
                    delete_permission_code = 'can_delete'
                    )
    """

    def __init__(self, *args, **kwargs):
        # Allow for authorization to be delegated through a property on the object
        self.parent_property = kwargs.pop('delegate_to_property', None)
        self.view_permission_code = kwargs.pop("view_permission_code", 'can_view')
        self.create_permission_code = kwargs.pop("create_permission_code", 'can_create')
        self.update_permission_code = kwargs.pop("update_permission_code", 'can_update')
        self.delete_permission_code = kwargs.pop("delete_permission_code", 'can_delete')
        super(GuardianAuthorization, self).__init__(**kwargs)

    def resolve_property(self, obj, property_path):
        path = property_path.split('.')
        ret = obj
        for p in path:
            if hasattr(ret, p):
                ret = getattr(ret, p)
            else:
                raise PropertyResolutionFailedException(property_path, obj.__class__)
        return ret

    def generic_base_check(self, object_list, bundle):
        """
            Returns False if either:
                a) if the `object_list.model` doesn't have a `_meta` attribute
                b) the `bundle.request` object doesn have a `user` attribute
        """
        klass = self.base_checks(bundle.request, object_list.model)
        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")
        return True

    def generic_item_check(self, object_list, bundle, permission):
        if bundle.request.user.is_superuser:
            return True

        if not self.generic_base_check(object_list, bundle):
            raise Unauthorized("You are not allowed to access that resource.")

        checker = ObjectPermissionChecker(bundle.request.user)
        if self.parent_property:
            obj = self.resolve_property(bundle.obj, self.parent_property)
        else:
            obj = bundle.obj

        # When the property resolves to None, prevent access by default
        if obj is None or not checker.has_perm(permission, obj):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def generic_list_check(self, object_list, bundle, permission):
        if not self.generic_base_check(object_list, bundle):
            raise Unauthorized("You are not allowed to access that resource.")
        user = bundle.request.user
        return [i for i in object_list if permission is None or user.has_perm(permission, i) or user.is_superuser]

    def generic_post_check(self, object_list, bundle, permission):
        if not self.generic_base_check(object_list, bundle):
            raise Unauthorized("You are not allowed to access that resource.")
        user = bundle.request.user
        if not user.has_perm(permission):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    # List Checks
    def create_list(self, object_list, bundle):
        return self.generic_list_check(object_list, bundle,
                                       self.create_permission_code)

    def read_list(self, object_list, bundle):
        if not self.view_permission_code:
            return object_list

        return self.generic_list_check(object_list, bundle,
                                       self.view_permission_code)

    def update_list(self, object_list, bundle):
        return self.generic_list_check(object_list, bundle,
                                       self.update_permission_code)

    def delete_list(self, object_list, bundle):
        return self.generic_list_check(object_list, bundle,
                                       self.delete_permission_code)

    # Item Checks
    def create_detail(self, object_list, bundle):
        return self.generic_item_check(object_list, bundle,
                                       self.create_permission_code)

    def read_detail(self, object_list, bundle):
        if not self.view_permission_code:
            return True
        return self.generic_item_check(object_list, bundle,
                                       self.view_permission_code)

    def update_detail(self, object_list, bundle):
        return self.generic_item_check(object_list, bundle,
                                       self.update_permission_code)

    def delete_detail(self, object_list, bundle):
        return self.generic_item_check(object_list, bundle,
                                       self.delete_permission_code)

class NfirsResource(Resource):
    """
    NFIRS-specific API calls
    """
    class Meta:
        resource_name = 'nfirs'
        authentication = ApiKeyAuthentication()
        list_allowed_methods = ['get', 'post']
        serializer = PrettyJSONSerializer()

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/update%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('update_nfirs'), name="api_update_nfirs"),
            url(r"^(?P<resource_name>%s)/refresh%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('refresh_nfirs'), name="api_refresh_nfirs"),
        ]

    def update_nfirs(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        years = None
        if request.GET.get('years'):
            years = [int(year) for year in request.GET.get('years').split(',')]

        if request.GET.get('department_id'):
            args = (request.GET.get('department_id'), years)

            existing_tasks = task_exists('update_nfirs_counts', args)

            # make sure the task is not already being processed
            if not existing_tasks:
                task = update_nfirs_counts.apply_async(args=args)
            else:
                task = existing_tasks[0]
        else:
            args = (years,)

            existing_tasks = task_exists('update_all_nfirs_counts', args)

            # make sure the task is not already being processed
            if not existing_tasks:
                task = update_all_nfirs_counts.apply_async(args=args)
            else:
                task = existing_tasks[0]

        task_info = task if isinstance(task, dict) else {
            'id': task.id,
            'state': task.state,
            'status': task.status,
        }

        return HttpResponse(
            json.dumps(task_info),
            content_type='application/json',
        )

    def refresh_nfirs(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        view_name = None
        task = None

        if request.GET.get('name'):
            view_name = request.GET.get('name')

        args = (view_name,)

        existing_tasks = task_exists('refresh_nfirs_views', args)

        # make sure the task is not already being processed
        if not existing_tasks:
            task = refresh_nfirs_views.apply_async(args=args)
        else:
            task = existing_tasks[0]

        task_info = task if isinstance(task, dict) else {
            'id': task.id,
            'state': task.state,
            'status': task.status,
        }

        return HttpResponse(
            json.dumps(task_info),
            content_type='application/json',
        )

class FireDepartmentResource(JSONDefaultModelResourceMixin, ModelResource):
    """
    The Fire Department API.
    """

    class Meta:
        readonly_fields = ['owned_tracts_geom']
        resource_name = 'fire-departments'
        queryset = FireDepartment.objects.defer('owned_tracts_geom').filter(archived=False)
        authorization = GuardianAuthorization(view_permission_code=None,
                                              update_permission_code='change_firedepartment',
                                              create_permission_code='change_firedepartment',
                                              delete_permission_code='admin_firedepartment')
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache()
        list_allowed_methods = ['get', 'put']
        detail_allowed_methods = ['get', 'put']
        filtering = {'state': ALL, 'featured': ALL, 'fdid': ALL, 'id': ALL}
        serializer = PrettyJSONSerializer()
        limit = 120
        max_limit = 2000

    def __init__(self, **kwargs):
        super(FireDepartmentResource, self).__init__(**kwargs)
        for f in getattr(self.Meta, 'readonly_fields', []):
            self.fields[f].readonly = True

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\w[\w/-]*)/grafana%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_grafana_line'), name="api_get_name"),
        ]

    def get_grafana_line(self, request, **kwargs):
        self.method_check(request, allowed=['get', 'options'])
        self.is_authenticated(request)

        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        if request.method == 'options':
            return response

        try:
            bundle = self.build_bundle(data={'pk': kwargs['pk']}, request=request)
            obj = self.cached_obj_get(bundle=bundle, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
            return HttpGone()
        except MultipleObjectsReturned:
            return HttpMultipleChoices("More than one resource is found at this URI.")

        response.content = '<h2>{}</h2><span>FDID: {} STATE: {} POPULATION: {}</span>'.format(obj.name, obj.fdid, obj.state, obj.population)
        return response

    def hydrate_geom(self, bundle):
        try:
            geom = bundle.data.get('geom')
            boundary = geos.GEOSGeometry(json.dumps(geom))
            if type(boundary) is geos.Polygon:
                bundle.data['geom'] = json.loads(geos.MultiPolygon(boundary).json)
        except Exception:
            bundle.data['geom'] = None
        return bundle

    def dehydrate(self, bundle):
        """
        remove fields not requested

        note: this is called for every object, so works for both detail and
              list requests
        """
        only_fields = bundle.request.GET.get('fields')
        debug_fields = bundle.request.GET.get('fields_debug', False)
        if only_fields:
            only_fields = only_fields.split(',')
            fields_to_remove = [field for field in bundle.data.keys()
                                if field not in only_fields]
            for field in fields_to_remove:
                del bundle.data[field]
            if debug_fields:
                bundle.data['_fields_selected'] = [field for field in only_fields
                                                   if field in bundle.data.keys()]
                bundle.data['_fields_removed'] = fields_to_remove
        return bundle


class FireStationResource(JSONDefaultModelResourceMixin, ModelResource):
    """
    The Fire Station API.
    """

    department = fields.ForeignKey(FireDepartmentResource, 'department', null=True)

    class Meta:
        resource_name = 'firestations'

        queryset = FireStation.objects.all()
        authorization = GuardianAuthorization(delegate_to_property='department',
                                              view_permission_code=None,
                                              update_permission_code='change_firedepartment',
                                              create_permission_code='change_firedepartment',
                                              delete_permission_code='admin_firedepartment')
        authentication = MultiAuthentication(Authentication(), SessionAuthentication(), ApiKeyAuthentication())
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'put']
        filtering = {'department': ('exact',), 'state': ('exact',), 'id': ('exact',), 'fdid': ('exact',)}
        excludes = ['addressbuildingname', 'complex_id', 'data_security', 'distribution_policy', 'fcode', 'foot_id',
                    'ftype', 'globalid', 'gnis_id', 'islandmark', 'loaddate', 'objectid', 'permanent_identifier',
                    'pointlocationtype', 'source_datadesc', 'source_datasetid', 'source_featureid',
                    'source_originator', 'admintype'
                    ]
        serializer = PrettyJSONSerializer()
        limit = 120

    def hydrate_district(self, bundle):
        try:
            geom = bundle.data.get('district')
            boundary = geos.GEOSGeometry(json.dumps(geom))
            if type(boundary) is geos.Polygon:
                boundary = geos.MultiPolygon(boundary)
            bundle.data['district'] = json.loads(boundary.json)
        except Exception:
            bundle.data['district'] = None
        return bundle

    def prepend_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/(?P<pk>\d+)/service-area%s" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_service_areas'), name="api_get_firestation_service_areas"),
        ]

    def get_service_areas(self, request, **kwargs):
        self.method_check(request, allowed=['get', 'options'])
        self.is_authenticated(request)

        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Content-Type'

        if request.method == 'options':
            return response

        try:
            firestation = FireStation.objects.get(pk=kwargs['pk'])
        except DoesNotExist as e:
            return HttpResponse(
                status=404,
                reason='Station {} not found'.format(kwargs['pk'])
            )

        service_area_attrs = sorted(attr for attr in dir(firestation) if attr.startswith('service_area'))
        service_area_geoms = { service_area_attr: getattr(firestation, service_area_attr, None) for service_area_attr in service_area_attrs }

        # if the service area geometries are not in the database, fetch them from mapbox and
        # cache them in the database
        if not all(service_area_geoms.values()):
            # make requests to mapbox and store the service areas
            url = '{base_url}/isochrone/v1/mapbox/driving/{x},{y}'.format(
                x=round(firestation.geom.x, 5),
                y=round(firestation.geom.y, 5),
                base_url=MAPBOX_BASE_URL,
            )

            for service_area in service_area_geoms:
                params = {
                    'contours_minutes': re.findall(r'\d+$', service_area)[0],
                    'polygons': 'true',
                    'access_token': MAPBOX_ACCESS_TOKEN,
                }

                res = requests.get(url, params=params)

                if 'features' not in res.json():
                    return HttpResponse(
                        status=404,
                        reason='No matching service area geometries found for this station\'s location'
                    )

                raw_geometry = json.dumps(res.json()['features'][0]['geometry'])
                isochrone_geom = geos.GEOSGeometry(raw_geometry).buffer(0)

                service_area_geoms[service_area] = isochrone_geom

            for i in reversed(range(1, len(service_area_attrs))):
                service_area_geoms[service_area_attrs[i]] = service_area_geoms[service_area_attrs[i]].difference(service_area_geoms[service_area_attrs[i-1]])

            # some may be Polygons, need to coerce them to MultiPolygon
            for service_area, service_area_geom in service_area_geoms.items():
                geom = to_multipolygon(service_area_geom)
                setattr(firestation, service_area, geom)
                service_area_geoms[service_area] = geom

            firestation.save(update_fields=service_area_geoms.keys())

        return HttpResponse(
            json.dumps({ k: json.loads(v.geojson) for k, v in service_area_geoms.items() }),
            content_type='application/json',
        )

class StaffingResource(JSONDefaultModelResourceMixin, ModelResource):
    """
    The ResponseCapability API.
    """

    firestation = fields.ForeignKey(FireStationResource, 'firestation')

    class Meta:
        resource_name = 'staffing'
        queryset = Staffing.objects.all()
        authorization = GuardianAuthorization(delegate_to_property='firestation.department',
                                              view_permission_code=None,
                                              update_permission_code='change_firedepartment',
                                              create_permission_code='change_firedepartment',
                                              delete_permission_code='change_firedepartment')
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering = {'firestation': ALL}
        validation = FormValidation(form_class=StaffingForm)
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        serializer = PrettyJSONSerializer()
        always_return_data = True


class StaffingStationRollupResource(JSONDefaultModelResourceMixin, ModelResource):
    """
    Merges Staffing Data with the Station Data
    """

    department = fields.ForeignKey(FireDepartmentResource, 'department', null=True)
    staffingdata = fields.ToManyField('firecares.firestation.api.StaffingResource', 'staffing_set', full=True)

    class Meta:
        resource_name = 'staffingstations'
        queryset = FireStation.objects.all()

        authorization = GuardianAuthorization(delegate_to_property='department',
                                              view_permission_code=None,
                                              update_permission_code='change_firedepartment',
                                              create_permission_code='change_firedepartment',
                                              delete_permission_code='admin_firedepartment')
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'put']
        filtering = {'department': ('exact',), 'state': ('exact',), 'id': ('exact',)}
        excludes = ['addressbuildingname', 'complex_id', 'data_security', 'distribution_policy', 'fcode', 'foot_id',
                    'ftype', 'globalid', 'gnis_id', 'islandmark', 'loaddate', 'objectid', 'permanent_identifier',
                    'pointlocationtype', 'source_datadesc', 'source_datasetid', 'source_featureid', 'zipcode', 'department',
                    'source_originator', 'admintype', 'district', 'archived', 'modified', 'state', 'address', 'city'
                    ]
        serializer = PrettyJSONSerializer()
        limit = 140


class WeatherWarningResource(JSONDefaultModelResourceMixin, ModelResource):
    """
    The Weather API mege with department id.
    """
    department = fields.ForeignKey(FireDepartmentResource, 'department', null=True)

    class Meta:
        resource_name = 'weather-warning'
        queryset = DepartmentWarnings.objects.all()
        authorization = GuardianAuthorization(delegate_to_property='department',
                                              view_permission_code=None,
                                              update_permission_code='change_firedepartment',
                                              create_permission_code='change_firedepartment',
                                              delete_permission_code='change_firedepartment')
        filtering = {
            'department': ('exact',),
            'state': ('exact',),
            'id': ('exact',),
            'issuedate': ('exact', 'range'),
            'warngeom': ALL,
        }
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get']
        cache = SimpleCache(timeout=120)
        serializer = PrettyJSONSerializer()
        always_return_data = True

    def build_filters(self, filters=None, **kwargs):
        allow_geodjango_filters(self._meta)
        return super(WeatherWarningResource, self).build_filters(filters)

    def get_object_list(self, request):
        return super(WeatherWarningResource, self).get_object_list(request).filter(expiredate__gte=timezone.now())


class GetServiceAreaInfo(JSONDefaultModelResourceMixin, ModelResource):
    """
    Get Service area info based on Drive Times for Department ID
    """
    department = fields.ForeignKey(FireDepartmentResource, 'department', null=True)

    class Meta:
        resource_name = 'getserviceareainfo'
        authorization = GuardianAuthorization(delegate_to_property='department',
                                              view_permission_code=None,
                                              update_permission_code='change_firedepartment',
                                              create_permission_code='change_firedepartment',
                                              delete_permission_code='change_firedepartment')

        #  Return the departement rollup info for service areas
        queryset = ParcelDepartmentHazardLevel.objects.all()

        filtering = {'department': ('exact',), 'id': ('exact',)}
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post']
        serializer = PrettyJSONSerializer()
        always_return_data = True


class GetEFFFInfo(JSONDefaultModelResourceMixin, ModelResource):
    """
    Get effective fire fighting force info based on Drive Times for Department ID
    """
    department = fields.ForeignKey(FireDepartmentResource, 'department', null=True)

    class Meta:
        resource_name = 'getefffinfo'
        authorization = GuardianAuthorization(delegate_to_property='department',
                                              view_permission_code=None,
                                              update_permission_code='change_firedepartment',
                                              create_permission_code='change_firedepartment',
                                              delete_permission_code='change_firedepartment')

        #  Return the departement rollup info for effective fire fighting force
        queryset = EffectiveFireFightingForceLevel.objects.all()

        filtering = {'department': ('exact',), 'id': ('exact',)}
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post']
        serializer = PrettyJSONSerializer()
        always_return_data = True
