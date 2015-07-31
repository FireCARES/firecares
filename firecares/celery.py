
from __future__ import absolute_import
import boto
import os
import mimetypes
import requests
from celery import Celery
from django.conf import settings
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from django.utils.text import slugify
from firecares.utils.s3put import singlepart_upload
from firecares.firestation.models import FireDepartment
from firecares.firestation.models import NFIRSStatistic as nfirs
from firecares.utils import convert_png_to_jpg
from celery.task import current

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'firecares.settings.local')

app = Celery('firecares')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


def download_file(url, download_to=None):

    if not download_to:
        download_to = url.split('/')[-1]

    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(os.path.join(download_to, download_to), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return download_to



@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

@app.task(rate_limit=10)
def cache_thumbnail(id, upload_to_s3=False, marker=True):
    try:
        import shutil
        print settings.MAPBOX_ACCESS_TOKEN
        from firecares.firestation.models import FireDepartment
        department = FireDepartment.objects.get(id=id)

        filename = department.thumbnail_name
        generate_thumbnail = department.generate_thumbnail(marker=marker)

        if not marker:
            filename = department.thumbnail_name_no_marker

        full_filename = os.path.join('/home/firecares/department-thumbnails', filename)

        if not generate_thumbnail.startswith('/static'):
            f = download_file(generate_thumbnail, full_filename.replace('jpg', 'png'))
            full_filename = convert_png_to_jpg(f)
        else:
            shutil.copy('/webapps/firecares/firecares/firecares/firestation/static/firestation/theme/assets/images/content/property-1.jpg', full_filename)

        if upload_to_s3:
            c = boto.s3.connect_to_region('us-east-1',
                                          aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                                          aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                                          is_secure=True,
                                          calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                                          debug=2
                                          )

            b = c.get_bucket('firecares-static/department-thumbnails', validate=False)
            mtype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            headers = {'Content-Type': mtype, 'Cache-Control': 'max-age=%d, public' % (3600 * 24)}
            singlepart_upload(b,
                              key_name=filename,
                              fullpath=full_filename,
                              policy='public-read',
                              reduced_redundancy=False,
                              headers=headers)

    except Exception as exc:
        if current.request.retries < 3:
            current.retry(exc=exc, countdown=min(2 ** current.request.retries, 128))

@app.task
def update_nfirs_counts(id):

        if not id:
            return

        try:
            fd = FireDepartment.objects.get(id=id)
            cursor = connections['nfirs'].cursor()

        except (FireDepartment.DoesNotExist, ConnectionDoesNotExist):
            return

        civilan_casualities = {2002: None,
                               2003: None,
                               2004: None,
                               2005: None,
                               2006: None,
                               2007: None,
                               2008: None,
                               2009: None,
                               2010: None,
                               2011: None,
                               2012: None}

        cursor.execute("select extract(year from inc_date) as year, count(*) from civiliancasualty where fdid=%s and state=%s"
                              "  group by year order by year desc;", (fd.fdid, fd.state))

        results = cursor.fetchall()
        for year, count in results:
            civilan_casualities[year] = count

        for year, count in civilan_casualities.items():
            nfirs.objects.update_or_create(year=year, defaults={'count': count},
                                           fire_department=fd, metric='civilian_casualties')

        residential_fires = {2002: None,
                             2003: None,
                             2004: None,
                             2005: None,
                             2006: None,
                             2007: None,
                             2008: None,
                             2009: None,
                             2010: None,
                             2011: None,
                             2012: None}

        cursor.execute("select extract(year from inc_date) as year, count(*) from buildingfires where fdid=%s and state=%s"
                              "  group by year order by year desc;", (fd.fdid, fd.state))

        results = cursor.fetchall()
        for year, count in results:
            residential_fires[year] = count

        for year, count in residential_fires.items():
            nfirs.objects.update_or_create(year=year, defaults={'count': count},
                                           fire_department=fd, metric='residential_structure_fires')
