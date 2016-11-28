import json
import logging
from .forms import StaffingForm
from .models import FireStation, Staffing, FireDepartment
from django.core.serializers.json import DjangoJSONEncoder
from tastypie import fields
from tastypie.authentication import SessionAuthentication, ApiKeyAuthentication, MultiAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.constants import ALL
from tastypie.contrib.gis.resources import ModelResource
from tastypie.exceptions import Unauthorized
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


# Pulled from https://gist.github.com/7wonders/6557760
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
                    view_permission_code = 'can_view',
                    create_permission_code = 'can_create',
                    update_permission_code = 'can_update',
                    delete_permission_code = 'can_delete'
                    )
    """

    def __init__(self, *args, **kwargs):
        # Allow for authorization to be delegated through a property on the object
        if 'parent_property' in kwargs:
            self.parent_property = kwargs.pop('parent_property')
        self.view_permission_code = kwargs.pop("view_permission_code", 'can_view')
        self.create_permission_code = kwargs.pop("create_permission_code", 'can_create')
        self.update_permission_code = kwargs.pop("update_permission_code", 'can_update')
        self.delete_permission_code = kwargs.pop("delete_permission_code", 'can_delete')
        super(GuardianAuthorization, self).__init__(**kwargs)

    def generic_base_check(self, object_list, bundle):
        """
            Returns False if either:
                a) if the `object_list.model` doesn't have a `_meta` attribute
                b) the `bundle.request` object doesn have a `user` attribute
        """
        #TODO: Override w/ class of parent property
        klass = self.base_checks(bundle.request, object_list.model)
        if klass is False:
            raise Unauthorized("You are not allowed to access that resource.")
        return True

    def generic_item_check(self, object_list, bundle, permission):
        if not self.generic_base_check(object_list, bundle):
            raise Unauthorized("You are not allowed to access that resource.")

        checker = ObjectPermissionChecker(bundle.request.user)
        #TODO: Override w/ parent property
        if not checker.has_perm(permission, bundle.obj):
            raise Unauthorized("You are not allowed to access that resource.")

        return True

    def generic_list_check(self, object_list, bundle, permission):
        if not self.generic_base_check(object_list, bundle):
            raise Unauthorized("You are not allowed to access that resource.")
        user = bundle.request.user
        return [i for i in object_list if user.has_perm(permission, i)]

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
        return self.generic_post_check(object_list, bundle,
                                       self.create_permission_code)

    def read_detail(self, object_list, bundle):
        return self.generic_item_check(object_list, bundle,
                                       self.view_permission_code)

    def update_detail(self, object_list, bundle):
        return self.generic_item_check(object_list, bundle,
                                       self.update_permission_code)

    def delete_detail(self, object_list, bundle):
        return self.generic_item_check(object_list, bundle,
                                       self.delete_permission_code)


class FireDepartmentResource(ModelResource):
    """
    The Fire Department API.
    """

    class Meta:
        resource_name = 'fire-departments'
        queryset = FireDepartment.objects.filter(archived=False)
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'put']
        filtering = {'state': ALL, 'featured': ALL}
        serializer = PrettyJSONSerializer()
        limit = 120


class FireStationResource(JSONDefaultModelResourceMixin, ModelResource):
    """
    The Fire Station API.
    """

    department = fields.ForeignKey(FireDepartmentResource, 'department', null=True)

    class Meta:
        resource_name = 'firestations'
        queryset = FireStation.objects.all()
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get', 'put']
        filtering = {'department': ('exact',), 'state': ('exact',), 'id': ('exact',)}
        excludes = ['addressbuildingname', 'complex_id', 'data_security', 'distribution_policy', 'fcode', 'foot_id',
                    'ftype', 'globalid', 'gnis_id', 'islandmark', 'loaddate', 'objectid', 'permanent_identifier',
                    'pointlocationtype', 'source_datadesc', 'source_datasetid', 'source_featureid', 'source_originator',
                    'admintype', 'district'
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
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        filtering = {'firestation': ALL}
        validation = FormValidation(form_class=StaffingForm)
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'put', 'delete']
        serializer = PrettyJSONSerializer()
        always_return_data = True
