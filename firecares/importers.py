from osgeo_importer.importers import Import, GDALInspector
from osgeo_importer.inspectors import NoDataSourceFound
from django.contrib.gis.gdal import DataSource
from firecares.firestation.models import FireDepartment, FireStation, Staffing
from firecares.firecares_core.models import Address, Country
from django.db import transaction


class GeoDjangoInspector(GDALInspector):

    def __init__(self, connection_string, *args, **kwargs):
        self.file = connection_string
        self.data = None
        super(GeoDjangoInspector, self).__init__(connection_string, *args, **kwargs)

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
            'name': 'name',
            'department': 'department',
            'station_nu': 'station_number',
            'address_l1': 'station_address__address_line1',
            'address_l2': 'station_address__address_line2',
            'country': 'station_address__country',
            'state': 'station_address__state_province',
            'city': 'station_address__city',
            'zipcode': 'station_address__postal_code',
            'id': 'id',
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
                    object = FireStation.objects.get(**mapping)
                except FireStation.DoesNotExist:
                    object, created = FireStation.objects.update_or_create(id=mapping['id'], defaults=mapping)
                    results.append([object, {}])

                self.populate_staffing(feature, object)

            return results

    @staticmethod
    def populate_staffing(feature, station):
        """
        Populates staffing records from a feature.

        Note: This replaces all staffing records vs updating existing records.
        """
        staffing_fields = dict(Staffing.APPARATUS_SHAPEFILE_CHOICES)
        staffing_fields_aliases = dict((v, k) for k, v in staffing_fields.iteritems())

        with transaction.atomic():

            # Delete existing staffing objects
            Staffing.objects.filter(firestation=station).delete()

            for field in feature.fields:
                for alias in staffing_fields_aliases.keys():

                    if field.startswith(alias):
                        staffing_value = feature.get(field)

                        if not staffing_value:
                            continue

                        if field[-1].isdigit():
                            field = field.rsplit('_', 1)[0]

                        Staffing.objects.create(apparatus=staffing_fields_aliases[field],
                                                personnel=staffing_value, firestation=station)

    @property
    def import_router(self):
        return self.import_stations

    @transaction.atomic()
    def import_file(self, *args, **kwargs):
        return self.import_router(*args, **kwargs)
