import glob
import os
import sys

sys.path.append(os.pardir)

from firecares.firestation.management.commands.match_districts import Command  # noqa
from firecares.firestation.models import FireDepartment  # noqa
from django.contrib.gis.geos import GeometryCollection as GC  # noqa
import django  # noqa

django.setup()
files = glob.glob(sys.argv[1] + '*districts*.geojson')

parsed_files = [(n.split('-')[1].upper(), n.split('-')[2], n) for n in files]

for state, name, path in parsed_files:
    department = None

    try:
        department = FireDepartment.priority_departments.get(state=state, name__icontains=name.replace('_', ' '))
    except FireDepartment.DoesNotExist:
        if name == 'los_angeles_city':
            department = FireDepartment.objects.get(id=87256)

    c = Command()
    c.handle(geojson_file=path, queryset=department.firestation_set.all())
    geometry_collection = GC([n for n in department.firestation_set.all().values_list('district', flat=True) if n])
    map(geometry_collection.append, [n for n in department.firestation_set.all().values_list('geom', flat=True) if n])

    with open(os.path.join(sys.argv[1], 'processed', 'us-{0}-{1}-disticts_processed.geojson'.format(state.lower(), name, department.name.replace(' ', '_').lower())), 'w') as output:
        output.write(geometry_collection.json)
