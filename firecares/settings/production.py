from firecares.settings.base import *

INSTALLED_APPS = (
    'django_statsd',
) + INSTALLED_APPS

STATSD_HOST = 'stats.garnertb.com'
STATSD_PREFIX = 'firecares'

STATSD_PATCHES = [
    'django_statsd.patches.db',
    'django_statsd.patches.cache',
]

MIDDLEWARE_CLASSES = (
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'django_statsd.middleware.TastyPieRequestTimingMiddleware'
) + MIDDLEWARE_CLASSES

STATSD_PATCHES = [
        'django_statsd.patches.db',
        'django_statsd.patches.cache',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

AWS_STORAGE_BUCKET_NAME = 'firecares-static'
COMPRESS_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
COMPRESS_URL = "https://s3.amazonaws.com/firecares-static/"
COMPRESS_STORAGE = "firecares.utils.CachedS3BotoStorage"
STATICFILES_STORAGE = "firecares.utils.CachedS3BotoStorage"
STATIC_URL = COMPRESS_URL
DEBUG = False
AWS_QUERYSTRING_AUTH = False

try:
    from local_settings import *  # noqa
except ImportError:
    pass