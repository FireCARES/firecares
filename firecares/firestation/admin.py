from .models import FireStation, FireDepartment, Staffing, Document, IntersectingDepartmentLog
from firecares.firecares_core.models import Address
from firecares.firecares_core.admin import LocalOpenLayersAdmin
from django.contrib.gis import admin
from autocomplete_light import ModelForm as AutocompleteModelForm
from reversion.admin import VersionAdmin


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
                       'gnis_id', 'foot_id', 'complex_id']


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


class FireDepartmentAdmin(VersionAdmin, LocalOpenLayersAdmin):
    form = FireDepartmentAdminForm
    search_fields = ['name']
    list_display = ['name', 'state', 'created', 'modified']
    list_filter = ['state']


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

admin.site.register(FireStation, FireStationAdmin)
admin.site.register(FireDepartment, FireDepartmentAdmin)
admin.site.register(Staffing, ResponseCapabilityAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(IntersectingDepartmentLog, IntersectingDepartmentLogAdmin)

