from .models import GovUnits, Reserve, NativeAmericanArea, IncorporatedPlace, UnincorporatedPlace, CountyorEquivalent, \
    MinorCivilDivision, StateorTerritoryHigh
from django.contrib.gis import admin


class GovUnitsAdmin(admin.OSMGeoAdmin):
    pass


class ReserveAdmin(admin.OSMGeoAdmin):
    search_fields = ['name']
    list_display = ['name', 'fcode', 'admintype']


class IncorporatedPlaceAdmin(admin.OSMGeoAdmin):
    search_fields = ['place_name', 'state_name', 'place_fipscode']
    list_display = [ 'place_name', 'state_name', 'fcode', 'place_fipscode']
    list_filter = [ 'state_name', 'fcode']


class CountyOrEquivalentAdmin(admin.OSMGeoAdmin):
    list_display = ['county_name', 'state_name', 'fcode', 'stco_fipscode']
    list_filter = ['state_name', 'fcode']
    search_fields = ['county_name', 'state_name', 'stco_fipscode']


class MinorCivilDivisionAdmin(admin.OSMGeoAdmin):
    list_display = ['minorcivildivision_name', 'state_name', 'fcode']
    list_filter = ['state_name', 'fcode']
    search_fields = ['minorcivildivision_name', 'state_name']

admin.site.register(Reserve, ReserveAdmin)
admin.site.register(IncorporatedPlace, IncorporatedPlaceAdmin)
admin.site.register(UnincorporatedPlace, IncorporatedPlaceAdmin)
admin.site.register(CountyorEquivalent, CountyOrEquivalentAdmin)
admin.site.register(MinorCivilDivision, MinorCivilDivisionAdmin)

for model in [GovUnits, NativeAmericanArea, StateorTerritoryHigh]:
    admin.site.register(model, GovUnitsAdmin)

