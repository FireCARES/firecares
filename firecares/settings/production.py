import os
from firecares.settings.base import *  # noqa
from celery.schedules import crontab
from cmreslogging.handlers import CMRESHandler
from requests_aws4auth import AWS4Auth


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': os.getenv('MEMCACHE_LOCATION', '127.0.0.1:11211'),
    }
}

AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN', None)
AWS_S3_URL_PROTOCOL = os.getenv('AWS_S3_URL_PROTOCOL', 'http:')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', None)
COMPRESS_URL = os.getenv("COMPRESS_URL", None)
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

if 'ELASTICSEARCH_HOST' in os.environ:
    LOGGING['handlers']['elasticsearch'] = {  # noqa
        'level': os.getenv('ELASTICSEARCH_LEVEL', 'INFO'),
        'class': 'cmreslogging.handlers.CMRESHandler',
        'hosts': [{'host': os.getenv('ELASTICSEARCH_HOST'), 'port': int(os.getenv('ELASTICSEARCH_PORT', 80))}],
        'es_index_name': 'firecares-logs',
        'index_name_frequency': CMRESHandler.IndexNameFrequency.DAILY,
        'es_additional_fields': {'App': 'firecares.org', 'Environment': 'production'},
        'auth_details': AWS4Auth(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, 'es'),  # noqa
        'auth_type': CMRESHandler.AuthType.BASIC_AUTH,
        'use_ssl': True
    }

    loggers = LOGGING['loggers']  # noqa

    for k, v in loggers.items():
        v.get('handlers').append('elasticsearch')

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
