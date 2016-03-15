from .models import FireStation, FireDepartment, Staffing
from firecares.firecares_core.models import Address
from firecares.firecares_core.admin import LocalOpenLayersAdmin
from django.forms import ModelForm
from django.contrib.gis import admin
from autocomplete_light import ModelForm as AutocompleteModelForm


class FireStationAdminForm(AutocompleteModelForm):
    def __init__(self, *args, **kwargs):
        super(FireStationAdminForm, self).__init__(*args, **kwargs)
        self.fields['station_address'].queryset = Address.objects.select_related().all()


class FireStationAdmin(LocalOpenLayersAdmin):
    form = FireStationAdminForm
    list_display = ['state', 'name']
    list_filter = ['state', 'ftype']
    search_fields = ['name', 'state', 'city']
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


class FireDepartmentAdmin(LocalOpenLayersAdmin):
    form = FireDepartmentAdminForm
    search_fields = ['name']
    list_display = ['name', 'state']
    list_filter = ['state']


class ResponseCapabilityAdmin(LocalOpenLayersAdmin):
    pass


admin.site.register(FireStation, FireStationAdmin)
admin.site.register(FireDepartment, FireDepartmentAdmin)
admin.site.register(Staffing, ResponseCapabilityAdmin)
