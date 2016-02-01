from .models import Address, ContactRequest, MediaItem
from django.contrib.gis import admin


class AddressAdmin(admin.OSMGeoAdmin):
    list_display = ['__unicode__']
    list_filter = ['state_province']
    search_fields = ['address_line1', 'state_province', 'city']


class ContactRequestAdmin(admin.OSMGeoAdmin):
    list_display = ['name', 'email', 'created_at']
    search_fields = ['name', 'email']

admin.site.register(Address, AddressAdmin)
admin.site.register(ContactRequest, ContactRequestAdmin)
admin.site.register(MediaItem)
