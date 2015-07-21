import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'firecares.settings'

from firecares.firestation.models import FireStation
import csv


x = 0
saved = 0
with open('usfa-census-national.csv', 'r') as csvfile:
    rows = csv.DictReader(csvfile)
    for row in rows:
        x += 1
        print 'Tried Count', x
        try:
            station = FireStation.objects.get(name=row['Fire Dept Name'], state=row['HQ State'])
            station.fdid = row['FDID']
            station.save()
            saved += 1
            print 'Saved Count', saved
        except FireStation.DoesNotExist:
            continue
        except FireStation.MultipleObjectsReturned:
            print 'Multiple objects returned for: ', row['Fire Dept Name'], row['HQ State']

