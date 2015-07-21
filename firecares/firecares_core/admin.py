from .models import Address
from django.contrib.gis import admin


class AddressAdmin(admin.OSMGeoAdmin):
    list_display = ['__unicode__']
    list_filter = ['state_province']
    search_fields = ['address_line1', 'state_province', 'city']


admin.site.register(Address, AddressAdmin)
