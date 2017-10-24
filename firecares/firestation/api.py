import json
import logging
from .forms import StaffingForm
from .models import FireStation, Staffing, FireDepartment, ParcelDepartmentHazardLevel
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.gis import geos
from tastypie import fields
from tastypie.authentication import SessionAuthentication, ApiKeyAuthentication, MultiAuthentication, Authentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.constants import ALL
from tastypie.contrib.gis.resources import ModelResource
from tastypie.exceptions import Unauthorized, TastypieError
from tastypie.serializers import Serializer
from tastypie.validation import FormValidation
from guardian.core import ObjectPermissionChecker

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
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'put']
        filtering = {'state': ALL, 'featured': ALL}
        serializer = PrettyJSONSerializer()
        limit = 120
        max_limit = 2000

    def __init__(self, **kwargs):
        super(FireDepartmentResource, self).__init__(**kwargs)
        for f in getattr(self.Meta, 'readonly_fields', []):
            self.fields[f].readonly = True

    def hydrate_geom(self, bundle):
        geom = bundle.data.get('geom')
        boundary = geos.GEOSGeometry(json.dumps(geom))
        if type(boundary) is geos.Polygon:
            bundle.data['geom'] = json.loads(geos.MultiPolygon(boundary).json)
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
        filtering = {'department': ('exact',), 'state': ('exact',), 'id': ('exact',)}
        excludes = ['addressbuildingname', 'complex_id', 'data_security', 'distribution_policy', 'fcode', 'foot_id',
                    'ftype', 'globalid', 'gnis_id', 'islandmark', 'loaddate', 'objectid', 'permanent_identifier',
                    'pointlocationtype', 'source_datadesc', 'source_datasetid', 'source_featureid',
                    'source_originator', 'admintype'
                    ]
        serializer = PrettyJSONSerializer()
        limit = 120


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
