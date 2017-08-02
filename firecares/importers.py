import boto
import os
from osgeo_importer.importers import Import, GDALInspector
from osgeo_importer.inspectors import NoDataSourceFound
from django.core.exceptions import ValidationError
from django.contrib.gis.gdal import DataSource
from firecares.firestation.models import FireDepartment, FireStation, Staffing
from firecares.firecares_core.models import Address, Country
from django.db import transaction
from tempfile import NamedTemporaryFile


class GeoDjangoInspector(GDALInspector):

    def __init__(self, connection_string, *args, **kwargs):
        self.file = connection_string
        self.data = None
        super(GeoDjangoInspector, self).__init__(connection_string, *args, **kwargs)

    def validate(self):
        if self.data is None:
            raise NoDataSourceFound

        if len(self.data) != 1:
            raise ValidationError('Expecting single layer, got {}'.format(len(self.data)))

        layer = self.data[0]

        # Ensure that all required columns are present
        required_fields = ['name', 'station_id', 'department', 'station_nu', 'address_l1', 'address_l2', 'city', 'state', 'zipcode', 'country']

        missing_fields = []
        for req in required_fields:
            if req not in layer.fields:
                missing_fields.append(req)

        if missing_fields:
            raise ValidationError('Missing fields: {}'.format(', '.join(missing_fields)))

        # All stations should have a department associated
        missing_departments = []
        for feature in layer:
            d_id = feature.get('department')
            if not FireDepartment.objects.filter(id=d_id).exists():
                missing_departments.append(d_id)

        if missing_departments:
            raise ValidationError('Invalid or unspecified department references: {}'.format(', '.join(map(str, missing_departments))))

        # All stations should either have an ID that exists or be zero
        missing_stations = []
        for feature in layer:
            s_id = feature.get('station_id')
            # DataSource automatically assigns an ID if the ID is missing based on the current row,
            # so we need to use "station_id" instead :/
            if not FireStation.objects.filter(id=s_id).exists() and s_id:
                missing_stations.append(s_id)

        for feature in layer:
            country = feature.get('country')
            if not country:
                raise ValidationError('Missing country')

        if missing_stations:
            raise ValidationError('Invalid station ID: {}'.format(', '.join(map(str, missing_stations))))

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

        self.validate()

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
        if hasattr(self, 'temp_path'):
            os.unlink(self.temp_path)


class GeoDjangoImport(Import):

    enabled_handlers = []
    source_inspectors = [GeoDjangoInspector]

    def __init__(self, filename, upload_file=None, *args, **kwargs):
        self.file = filename
        self.temp_file = None
        self.upload_file = upload_file

        # If we're stored on S3, then pull down to local node
        if self.upload_file and self.upload_file.upload.metadata:
            bucket, keyname = self.upload_file.upload.metadata.split(':')
            conn = boto.connect_s3()
            key = conn.get_bucket(bucket).get_key(keyname)

            with NamedTemporaryFile(delete=False, suffix=os.path.splitext(keyname)[1]) as tf:
                self.temp_file = tf.name
                key.get_contents_to_file(tf)
                self.file = tf.name

            conn.close()

    def update_station(self, station, mapping):
        for attr, value in mapping.items():
            setattr(station, attr, value)
        station.save()

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
            'station_id': 'id',
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
                        country, created = Country.objects.get_or_create(iso_code=address_fields['country'])
                        if created:
                            country.name = address_fields['country']
                            country.save()
                        address_fields['country'] = country
                        address, created = Address.objects.update_or_create(defaults=address_geom, **address_fields)
                        mapping['station_address'] = address
                        mapping['address'] = address.address_line1
                        mapping['city'] = address.city
                        mapping['state'] = address.state_province
                        mapping['zipcode'] = address.postal_code

                # GDAL's DataSource appears to automatically assign an id when it's missing :/.  This could have
                # unintended side-effects (eg. clobbering existing records) if not captured; however,
                # there is also potential that perfectly valid records w/ valid ids could be skipped in this case
                # as well (for low id numbers), so we need to use another column as the truth for station identifiers.
                station_id = mapping.pop('id')
                if station_id:
                    object = FireStation.objects.get(id=station_id)
                    self.update_station(object, mapping)
                else:
                    object = FireStation.objects.create(**mapping)
                    results.append([str(object), {}])

                self.populate_staffing(feature, object)

            if self.temp_file:
                os.unlink(self.temp_file)

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
