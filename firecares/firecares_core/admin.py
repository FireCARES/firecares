import autocomplete_light
from .models import Address, ContactRequest, AccountRequest, RegistrationWhitelist
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.gis import admin
from firecares.firecares_core.models import UserProfile, PredeterminedUser, DepartmentAssociationRequest

User = get_user_model()


class LocalOpenLayersAdmin(admin.OSMGeoAdmin):
    openlayers_url = settings.STATIC_URL + 'openlayers/OpenLayers.js'


class AddressAdmin(LocalOpenLayersAdmin):
    list_display = ['__unicode__']
    list_filter = ['state_province']
    search_fields = ['address_line1', 'state_province', 'city']


class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at']
    search_fields = ['name', 'email']


class AccountRequestAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    search_fields = ['email']
    form = autocomplete_light.modelform_factory(AccountRequest, fields='__all__')


class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    form = autocomplete_light.modelform_factory(UserProfile, fields='__all__')


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]


class DepartmentAssociationRequestAdmin(admin.ModelAdmin):
    model = DepartmentAssociationRequest
    form = autocomplete_light.modelform_factory(DepartmentAssociationRequest, fields='__all__')


class RegistrationWhitelistAdmin(admin.ModelAdmin):
    model = RegistrationWhitelist
    form = autocomplete_light.modelform_factory(RegistrationWhitelist, fields='__all__')


admin.site.register(Address, AddressAdmin)
admin.site.register(ContactRequest, ContactRequestAdmin)
admin.site.register(AccountRequest, AccountRequestAdmin)
admin.site.register(RegistrationWhitelist, RegistrationWhitelistAdmin)
admin.site.register(PredeterminedUser)
admin.site.register(DepartmentAssociationRequest, DepartmentAssociationRequestAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
