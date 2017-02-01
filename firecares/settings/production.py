import os
from firecares.settings.base import *  # noqa
from celery.schedules import crontab

INSTALLED_APPS = (
    'django_statsd',
) + INSTALLED_APPS  # noqa

STATSD_HOST = 'stats.garnertb.com'
STATSD_PREFIX = 'firecares'
STATSD_CELERY_SIGNALS = True

STATSD_PATCHES = [
    'django_statsd.patches.db',
    'django_statsd.patches.cache',
]

MIDDLEWARE_CLASSES = (
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'django_statsd.middleware.TastyPieRequestTimingMiddleware'
) + MIDDLEWARE_CLASSES  # noqa

STATSD_PATCHES = [
    'django_statsd.patches.db',
    'django_statsd.patches.cache',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': os.getenv('MEMCACHE_LOCATION', '127.0.0.1:11211'),
    }
}

AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', None)
COMPRESS_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
COMPRESS_URL = "https://static.firecares.org/"
COMPRESS_STORAGE = "firecares.utils.CachedS3BotoStorage"
STATICFILES_STORAGE = "firecares.utils.CachedS3BotoStorage"
STATIC_URL = COMPRESS_URL
DEBUG = False
AWS_QUERYSTRING_AUTH = False
EMAIL_USE_TLS = True

IMIS_SSO_LOGIN_URL = 'https://my.iaff.org/Web/Contacts/SignIn_withoutCreateNewAccount.aspx?doRedirect='
IMIS_SSO_SERVICE_URL = 'https://member.iaff.org/iaff_sso_prod/sso.asmx?WSDL'

HELIX_ROOT = 'https://www.myhelix.org'
HELIX_AUTHORIZE_URL = HELIX_ROOT + '/app/OAuth/Authorize'
HELIX_TOKEN_URL = HELIX_ROOT + '/App/Token'
HELIX_CLIENT_ID = '39913518'
HELIX_REDIRECT = 'https://firecares.org/oauth'
HELIX_LOGOUT_URL = HELIX_ROOT + '/App/logout/' + HELIX_CLIENT_ID
HELIX_WHOAMI_URL = HELIX_ROOT + '/App/api/v2/Account/WhoAmI'
HELIX_FUNCTIONAL_TITLE_URL = HELIX_ROOT + '/App/api/v2/Membership/FuncTitle/'


CELERYBEAT_SCHEDULE = {
    # Executes nightly at midnight.
    'cache_every_midnight': {
        'task': 'firecares.tasks.cache.cache_histogram_data',
        'schedule': crontab(minute=0, hour=0),
    },
    'ensure_valid_data_every_midnight': {
        'task': 'firecares.tasks.email.ensure_valid_data',
        'schedule': crontab(minute=0, hour=0),
    }
}

try:
    from local_settings import *  # noqa
except ImportError:
    pass
