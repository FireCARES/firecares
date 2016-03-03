from osgeo_importer.importers import Import, GDALInspector
from osgeo_importer.inspectors import InspectorMixin, NoDataSourceFound
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.geos import Point
from firecares.firestation.models import FireDepartment, FireStation, Staffing
from firecares.firecares_core.models import Address, Country
from django.db import transaction


class GeoDjangoInspector(GDALInspector):

    def __init__(self, connection_string, *args, **kwargs):
        self.file = connection_string
        self.data = None
        super(GeoDjangoInspector, self).__init__( connection_string, *args, **kwargs)

    def open(self, *args, **kwargs):
        """
        Opens the file.
        """
        filename = self.file

        prepare_method = 'prepare_{0}'.format(self.method_safe_filetype)

        if hasattr(self, prepare_method):
            # prepare hooks make extension specific modifications to input parameters
            filename, args, kwargs = getattr(self, prepare_method)(filename, *args, **kwargs)

        self.data = DataSource(filename, *args, **kwargs)

        if self.data is None:
            raise NoDataSourceFound

        return self.data

    def describe_fields(self):
        """
        Returns a dict of the layers with fields and field types.
        """

        opened_file = self.data
        description = []

        if not opened_file:
            opened_file = self.open()

        for n, layer in enumerate(opened_file):
            layer_description = {'name': layer.name,
                                 'feature_count': layer.num_feat,
                                 'fields': [],
                                 'index': n,
                                 'geom_type': layer.geom_type.name}

            for name, field_type in zip(layer.fields, [fld.__name__ for fld in layer.field_types]):
                field_desc = {'name': name, 'type': field_type}
                layer_description['fields'].append(field_desc)

            description.append(layer_description)

        return description

    def file_type(self):
        try:
            return self.data.driver.name
        except AttributeError:
            return

    def close(self, *args, **kwargs):
        self.data = None


class GeoDjangoImport(Import):

    enabled_handlers = []
    source_inspectors = [GeoDjangoInspector]

    def __init__(self, filename, upload_file=None, *args, **kwargs):
        self.file = filename
        self.upload_file = upload_file

    def import_stations(self, *args, **kwargs):
        """
        Parses incoming station records and updates internal objects.
        """
        data, _ = self.open_source_datastore(self.file, *args, **kwargs)

        field_mappings = {
            'NAME': 'name',
            'DEPARTMENT': 'department',
            'STATION_NU': 'station_number',
            'ADDRESS_LI': 'station_address__address_line1',
            'ADDRESS_01': 'station_address__address_line2',
            'COUNTRY_ID': 'station_address__country',
            'STATE_PROV': 'station_address__state_province',
            'CITY': 'station_address__city',
            'POSTAL_COD': 'station_address__postal_code',
            'FIRECARES_': 'id',
        }

        results = []
        for layer in data:

            for feature in layer:
                mapping = {}
                address_fields = {}

                mapping['geom'] = feature.geom.geos

                for dirty_name in set(field_mappings.keys()) & set(feature.fields):
                    cleaned_name = field_mappings[dirty_name]
                    value = feature.get(dirty_name)

                    if cleaned_name == 'department':
                        value = FireDepartment.objects.get(id=value)

                    if '__' in cleaned_name:
                        address_fields[cleaned_name.replace('station_address__', '')] = value or None

                    else:
                        mapping[cleaned_name] = value

                if address_fields:
                    address_geom = {'geom': feature.geom.geos}
                    if address_fields['country']:
                        country, created = Country.objects.get_or_create(name=address_fields['country'])
                        address_fields['country'] = country
                        address, created = Address.objects.update_or_create(defaults=address_geom, **address_fields)
                        mapping['station_address'] = address
                        mapping['address'] = address.address_line1
                        mapping['city'] = address.city
                        mapping['state'] = address.state_province
                        mapping['zipcode'] = address.postal_code

                try:
                    FireStation.objects.get(**mapping)
                except FireStation.DoesNotExist:
                    object, created = FireStation.objects.update_or_create(id=mapping['id'], defaults=mapping)
                    results.append([object, {}])

            return results

    def import_staffing(self, *args, **kwargs):
        """
        Parses incoming staffing records and updates internal objects.
        """
        data, _ = self.open_source_datastore(self.file, *args, **kwargs)

        field_mappings = {
            'ID': 'id',
            'APPARATUS': 'apparatus',
            'FF': 'firefighter',
            'FF_PARAMED': 'firefighter_paramedic',
            'FF_EMT': 'firefighter_emt',
            'CHIEF_OFFI': 'chief_officer',
            'OFFICER_PA': 'officer_paramedic',
            'EMS_EMT': 'ems_emt',
            'EMS_PARAME': 'ems_paramedic',
            'STATION': 'firestation__id',
            'OFFICER': 'officer',
            'EMS_SUPERV': 'ems_supervisor',
        }

        results = []
        for layer in data:
            for feature in layer:
                mapping = {}

                for dirty_name in set(field_mappings.keys()) & set(feature.fields):
                    cleaned_name = field_mappings[dirty_name]
                    value = feature.get(dirty_name)
                    #if value == 779:
                    #    import ipdb; ipdb.set_trace()

                    if cleaned_name == 'firestation__id' and value:
                        mapping['firestation'] = FireStation.objects.get(id=value)
                    else:
                        mapping[cleaned_name] = value

                try:
                    Staffing.objects.get(**mapping)
                except Staffing.DoesNotExist:
                    object, created = Staffing.objects.update_or_create(id=mapping['id'], defaults=mapping)
                    results.append([object, {}])

            return results

    @property
    def import_router(self):
        if '-staffing' in self.file:
            return self.import_staffing

        return self.import_stations

    @transaction.atomic()
    def import_file(self, *args, **kwargs):
        return self.import_router(*args, **kwargs)
