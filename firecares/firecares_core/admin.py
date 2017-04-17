import autocomplete_light
from .models import Address, ContactRequest, AccountRequest, RegistrationWhitelist
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.gis import admin
from import_export.admin import ExportMixin
from firecares.firecares_core.models import UserProfile, PredeterminedUser, DepartmentAssociationRequest

User = get_user_model()


class LocalOpenLayersAdmin(admin.OSMGeoAdmin):
    openlayers_url = settings.STATIC_URL + 'openlayers/OpenLayers.js'


class AddressAdmin(LocalOpenLayersAdmin):
    list_display = ['__unicode__']
    list_filter = ['state_province']
    search_fields = ['address_line1', 'state_province', 'city']

    def save_model(self, request, obj, form, change):
        if change:
            obj.geocode()
        super(AddressAdmin, self).save_model(request, obj, form, change)


class ContactRequestAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at']
    search_fields = ['name', 'email']


class AccountRequestAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ['email', 'created_at']
    search_fields = ['email']
    form = autocomplete_light.modelform_factory(AccountRequest, fields='__all__')


class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    form = autocomplete_light.modelform_factory(UserProfile, fields='__all__')


class UserAdmin(ExportMixin, BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    inlines = [ProfileInline]


class DepartmentAssociationRequestAdmin(ExportMixin, admin.ModelAdmin):
    model = DepartmentAssociationRequest
    form = autocomplete_light.modelform_factory(DepartmentAssociationRequest, fields='__all__')


class RegistrationWhitelistAdmin(ExportMixin, admin.ModelAdmin):
    model = RegistrationWhitelist
    form = autocomplete_light.modelform_factory(RegistrationWhitelist, fields='__all__')


class PredeterminedUserAdmin(ExportMixin, admin.ModelAdmin):
    model = PredeterminedUser
    form = autocomplete_light.modelform_factory(PredeterminedUser, fields='__all__')


admin.site.register(Address, AddressAdmin)
admin.site.register(ContactRequest, ContactRequestAdmin)
admin.site.register(AccountRequest, AccountRequestAdmin)
admin.site.register(RegistrationWhitelist, RegistrationWhitelistAdmin)
admin.site.register(PredeterminedUser, PredeterminedUserAdmin)
admin.site.register(DepartmentAssociationRequest, DepartmentAssociationRequestAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
