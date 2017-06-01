import autocomplete_light
from .models import FireStation, FireDepartment, Staffing, Document, IntersectingDepartmentLog, DataFeedback
from firecares.firecares_core.models import Address
from firecares.firecares_core.admin import LocalOpenLayersAdmin
from django.contrib.gis import admin
from autocomplete_light import ModelForm as AutocompleteModelForm
from reversion.admin import VersionAdmin
from guardian.admin import GuardedModelAdmin


class FireStationAdminForm(AutocompleteModelForm):
    def __init__(self, *args, **kwargs):
        super(FireStationAdminForm, self).__init__(*args, **kwargs)
        self.fields['station_address'].queryset = Address.objects.select_related().all()


class FireStationAdmin(VersionAdmin, LocalOpenLayersAdmin):
    form = FireStationAdminForm
    list_display = ['state', 'name', 'created', 'modified']
    list_filter = ['state', 'ftype']
    search_fields = ['name', 'state', 'city', 'id']
    readonly_fields = ['permanent_identifier', 'source_featureid', 'source_datasetid', 'objectid', 'globalid',
                       'gnis_id', 'foot_id', 'complex_id', 'address_point']

    def address_point(self, instance):
        return str(instance.geom)

    address_point.short_description = 'Address (lon, lat)'


class FireStationInline(admin.TabularInline):
    model = FireStation
    fk_name = 'department'
    extra = 0
    readonly_fields = ['permanent_identifier', 'source_featureid', 'source_datasetid', 'objectid', 'globalid',
                       'gnis_id', 'foot_id', 'complex_id']


class FireDepartmentAdminForm(AutocompleteModelForm):
    def __init__(self, *args, **kwargs):
        super(FireDepartmentAdminForm, self).__init__(*args, **kwargs)
        self.fields['headquarters_address'].queryset = Address.objects.select_related().all()
        self.fields['mail_address'].queryset = Address.objects.select_related().all()

    class Meta:
        model = FireDepartment
        fields = '__all__'
        autocomplete_exclude = ('government_unit',)


class FireDepartmentAdmin(GuardedModelAdmin, VersionAdmin, LocalOpenLayersAdmin):
    form = FireDepartmentAdminForm
    search_fields = ['name']
    list_display = ['name', 'state', 'created', 'modified', 'archived']
    list_filter = ['state', 'archived']


class ResponseCapabilityAdmin(LocalOpenLayersAdmin):
    list_display = ['__unicode__', 'created', 'modified', 'personnel', 'als']
    exclude = ['firestation']


class DocumentAdmin(admin.ModelAdmin):
    exclude = ["created"]
    list_display = ['filename', 'created', 'uploaded_by', 'department']
    list_filter = ['uploaded_by', 'created']

    class Meta:
        model = Document


class IntersectingDepartmentLogAdmin(admin.ModelAdmin):
    pass


class DataFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'firestation', 'created_at', 'message']
    list_filter = ['created_at']
    form = autocomplete_light.modelform_factory(DataFeedback, fields='__all__')


admin.site.register(FireStation, FireStationAdmin)
admin.site.register(FireDepartment, FireDepartmentAdmin)
admin.site.register(Staffing, ResponseCapabilityAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(IntersectingDepartmentLog, IntersectingDepartmentLogAdmin)
admin.site.register(DataFeedback, DataFeedbackAdmin)
