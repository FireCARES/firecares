import os
from firecares.settings.base import *  # noqa
from celery.schedules import crontab

ALLOWED_HOSTS = ['0.0.0.0']

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

SECRET_KEY = '$keb7sv^%c+_'

IMIS_SSO_LOGIN_URL = 'https://my.iaff.org/Web/Contacts/SignIn_withoutCreateNewAccount.aspx?doRedirect='
IMIS_SSO_SERVICE_URL = 'https://member.iaff.org/iaff_sso_prod/sso.asmx?WSDL'

HELIX_ROOT = 'https://helix.auth0.com'
HELIX_AUTHORIZE_URL = HELIX_ROOT + '/authorize'
HELIX_TOKEN_URL = HELIX_ROOT + '/oauth/token'
HELIX_CLIENT_ID = 'O06btCnCKS98g025ACAgbeSuilHS9Pxa'
HELIX_REDIRECT = 'https://firecares.org/oauth'
HELIX_LOGOUT_URL = HELIX_ROOT + '/v2/logout?client_id=' + HELIX_CLIENT_ID + '&returnTo=https://firecares.org/'
HELIX_WHOAMI_URL = HELIX_ROOT + '/App/api/v2/Account/WhoAmI'
HELIX_FUNCTIONAL_TITLE_URL = HELIX_ROOT + '/App/api/v2/Membership/FuncTitle/'

STATICSITEMAPS_URL = 'https://firecares.org/static/'
STATICSITEMAPS_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICSITEMAPS_ROOT_DIR = ''

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
    },
    'update_warnings_every_60_minutes': {
        'task': 'firecares.tasks.weather_task.collect_weather_noaa_warnings',
        'schedule': crontab(minute=0)
    },
    'update_warning_geometry_every_midnight': {
        'task': 'firecares.tasks.weather_task.cleanup_dept_weather_noaa_warnings',
        'schedule': crontab(minute=0, hour=0)
    },
    'update_department_views_every_midnight': {
        'task': 'firecares.tasks.update.refresh_department_views',
        'schedule': crontab(minute=0, hour=0)
    }
}

try:
    from local_settings import *  # noqa
except ImportError:
    pass
