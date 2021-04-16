
from __future__ import absolute_import

import os
import sys
import alog
import boto
import mimetypes
import requests
from ast import literal_eval
from celery import Celery
from django.conf import settings

from firecares.settings.base import REDIS_URL
from firecares.utils.s3put import singlepart_upload
from celery.task import current

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'firecares.settings')

app = Celery('firecares')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
config = app.config_from_object('django.conf:settings')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.BROKER_URL = REDIS_URL
app.conf.result_backend = REDIS_URL

def download_file(url, download_to=None):

    if not download_to:
        download_to = url.split('/')[-1]

    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(os.path.join(download_to, download_to), 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
    return download_to

def task_exists(name, args=None, kwargs=None):
    args = args or tuple()
    kwargs = kwargs or {}

    inspector = app.control.inspect()

    print 'inspector.app.backend.url: {}'.format(inspector.app.backend.url)
    sys.stdout.flush()

    def matches(task):
        if name not in task['name']:
            return False

        if args != literal_eval(task['args']):
            return False

        if kwargs != literal_eval(task['kwargs']):
            return False

        return True

    tasks = []

    for active_tasks in inspector.active().values():
        tasks.extend(active_tasks)

    for scheduled_tasks in inspector.scheduled().values():
        tasks.extend(scheduled_tasks)

    for reserved_tasks in inspector.reserved().values():
        tasks.extend(reserved_tasks)

    relevant_tasks = [t for t in tasks if matches(t)]

    return relevant_tasks or False

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


@app.task(rate_limit=10)
def cache_thumbnail(id, upload_to_s3=False, marker=True):
    try:
        import shutil
        from firecares.firestation.models import FireDepartment
        department = FireDepartment.objects.get(id=id)

        filename = department.thumbnail_name
        generate_thumbnail = department.generate_thumbnail(marker=marker)

        if not marker:
            filename = department.thumbnail_name_no_marker

        full_filename = os.path.join('/home/firecares/department-thumbnails', filename)

        if not generate_thumbnail.startswith('/static'):
            download_file(generate_thumbnail, full_filename)
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
