from .models import Address, ContactRequest, AccountRequest
from django.conf import settings
from django.contrib.gis import admin


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


admin.site.register(Address, AddressAdmin)
admin.site.register(ContactRequest, ContactRequestAdmin)
admin.site.register(AccountRequest, AccountRequestAdmin)
