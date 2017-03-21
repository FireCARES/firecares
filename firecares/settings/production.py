import os
from firecares.settings.base import *  # noqa
from celery.schedules import crontab

AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN', None)
AWS_S3_URL_PROTOCOL = os.getenv('AWS_S3_URL_PROTOCOL', 'http:')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', None)
COMPRESS_URL = os.getenv("COMPRESS_URL", None)
COMPRESS_STORAGE = "storages.backends.s3boto.S3BotoStorage"
STATICFILES_STORAGE = "storages.backends.s3boto.S3BotoStorage"
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

STATICSITEMAPS_URL = 'https://firecares.org/static/'
STATICSITEMAPS_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

CELERYBEAT_SCHEDULE = {
    # Executes nightly at midnight.
    'cache_every_midnight': {
        'task': 'firecares.tasks.cache.cache_histogram_data',
        'schedule': crontab(minute=0, hour=0),
    },
    'ensure_valid_data_every_midnight': {
        'task': 'firecares.tasks.email.ensure_valid_data',
        'schedule': crontab(minute=0, hour=0),
    },
    'update_sitemap_every_60_minutes': {
        'task': 'static_sitemaps.tasks.GenerateSitemap',
        'schedule': crontab(minute=0)
    }
}

try:
    from local_settings import *  # noqa
except ImportError:
    pass
