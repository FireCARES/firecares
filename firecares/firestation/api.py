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
from tastypie.serializers import Serializer
from tastypie.validation import FormValidation


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


class FireDepartmentResource(ModelResource):
    """
    The Fire Department API.
    """

    class Meta:
        resource_name = 'fire-departments'
        queryset = FireDepartment.objects.all()
        authorization = DjangoAuthorization()
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        cache = SimpleCache()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        filtering = {'state': ALL, 'featured': ALL}
        serializer = PrettyJSONSerializer()
        limit = 120


class FireStationResource(ModelResource):
    """
    The Fire Station API.
    """

    department = fields.ForeignKey(FireDepartmentResource, 'department', null=True)

    class Meta:
        resource_name = 'firestations'
        queryset = FireStation.objects.all()
        cache = SimpleCache()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        filtering = {'department': ('exact',), 'state': ('exact',)}
        excludes = ['addressbuildingname', 'complex_id', 'data_security', 'distribution_policy', 'fcode', 'foot_id',
                    'ftype', 'globalid', 'gnis_id', 'islandmark', 'loaddate', 'objectid', 'permanent_identifier',
                    'pointlocationtype', 'source_datadesc', 'source_datasetid', 'source_featureid', 'source_originator',
                    'admintype', 'district'
                    ]
        serializer = PrettyJSONSerializer()
        limit = 120


class StaffingResource(ModelResource):
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
