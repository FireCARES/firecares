from .models import Address, ContactRequest, AccountRequest, RegistrationWhitelist
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.gis import admin
from firecares.firecares_core.models import UserProfile, PredeterminedUser

User = get_user_model()


class LocalOpenLayersAdmin(admin.OSMGeoAdmin):
    openlayers_url = settings.STATIC_URL + 'openlayers/OpenLayers.js'


class AddressAdmin(LocalOpenLayersAdmin):
    list_display = ['__unicode__']
    list_filter = ['state_province']
    search_fields = ['address_line1', 'state_province', 'city']


class ContactRequestAdmin(LocalOpenLayersAdmin):
    list_display = ['name', 'email', 'created_at']
    search_fields = ['name', 'email']


class AccountRequestAdmin(LocalOpenLayersAdmin):
    list_display = ['email', 'created_at']
    search_fields = ['email']


class ProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]


admin.site.register(Address, AddressAdmin)
admin.site.register(ContactRequest, ContactRequestAdmin)
admin.site.register(AccountRequest, AccountRequestAdmin)
admin.site.register(RegistrationWhitelist)
admin.site.register(PredeterminedUser)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
