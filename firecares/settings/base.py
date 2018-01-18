import os
from kombu import Queue
import sys
DEBUG = True
TEMPLATE_DEBUG = DEBUG
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)
DEPARTMENT_ADMIN_VERIFIERS = (
    # ('Your Name', 'your_email@example.com'),
)

DATA_FEEDBACK_EMAILS = ()

MANAGERS = ADMINS
TESTING = sys.argv[1:2] == ['test']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DATABASE_NAME', 'firecares'),
        'USER': os.getenv('DATABASE_USER', 'firecares'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'password'),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    },
    'nfirs': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('NFIRS_DATABASE_NAME', 'nfirs'),
        'USER': os.getenv('NFIRS_DATABASE_USER', 'firecares'),
        'PASSWORD': os.getenv('NFIRS_DATABASE_PASSWORD', 'password'),
        'PORT': os.getenv('NFIRS_DATABASE_PORT', '5432'),
        'HOST': os.getenv('NFIRS_DATABASE_HOST', 'localhost'),
        'TEST': {
            'MIRROR': 'default'
        }
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = '/var/www/firecares/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/var/www/firecares/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '$keb7sv^%c+_7+94u6_!lc3%a-3ima9eh!xyj%$xa8yibv&ogr'

# Leave as empty to prevent captcha verification
RECAPTCHA_SECRET = ''

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.RemoteUserBackend'
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.i18n",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "firecares.firecares_core.context_processors.global_settings",
    "firecares.firecares_core.context_processors.fire_department_search",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'firecares.firecares_core.middleware.DisclaimerAcceptedMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'firecares.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'firecares.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'genericm2m',
    'autocomplete_light',
    'django.contrib.admin',
    'django.contrib.gis',
    'django.contrib.humanize',
    'firecares.firecares_core',
    'firecares.firestation',
    'firecares.usgs',
    'firecares.weather',
    'jsonfield',
    'compressor',
    'storages',
    'widget_tweaks',
    'firecares.tasks',
    'registration',
    'django_slack',
    'osgeo_importer',
    'djcelery',
    'reversion',
    'favit',
    'guardian',
    'django_nose',
    'invitations',
    'static_sitemaps',
    'import_export',
    'tastypie'
)

OSGEO_IMPORTER = 'firecares.importers.GeoDjangoImport'
OSGEO_INSPECTOR = 'firecares.importers.GeoDjangoInspector'
OSGEO_STORAGE_BUCKET_NAME = os.getenv('OSGEO_STORAGE_BUCKET_NAME', None)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(message)s',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'slack_admins': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'django_slack.log.SlackExceptionHandler'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'mail_admins', 'slack_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'osgeo_importer': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'firecares': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'firecares.firecares_core.views': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

TASTYPIE_DEFAULT_FORMATS = ['json', 'xml']

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--verbosity=2',
    '--nologcapture'
]

# Celery settings.
BROKER_URL = os.getenv('BROKER_URL', 'amqp://guest:guest@127.0.0.1//')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'amqp')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', None)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', None)
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', None)
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN', None)
GOOGLE_ANALYTICS_TRACKING_ID = os.getenv('GOOGLE_ANALYTICS_TRACKING_ID', None)

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login'
IMIS_SSO_LOGIN_URL = 'https://staging.iaff.org/Web/Contacts/SignIn_withoutCreateNewAccount.aspx?doRedirect='
IMIS_SSO_SERVICE_URL = 'https://member.iaff.org/iaff_sso_staging/sso.asmx?WSDL'

HELIX_ROOT = 'https://test.myhelix.org'
HELIX_AUTHORIZE_URL = HELIX_ROOT + '/app/OAuth/Authorize'
HELIX_TOKEN_URL = HELIX_ROOT + '/App/Token'
HELIX_SCOPE = ['basic']
HELIX_CLIENT_ID = '39913518'
HELIX_SECRET = os.getenv('HELIX_SECRET', None)
HELIX_REDIRECT = 'https://192.168.33.15:8000/oauth'
HELIX_LOGOUT_URL = HELIX_ROOT + '/App/logout/' + HELIX_CLIENT_ID
HELIX_WHOAMI_URL = HELIX_ROOT + '/App/api/v2/Account/WhoAmI'
HELIX_FUNCTIONAL_TITLE_URL = HELIX_ROOT + '/App/api/v2/Membership/FuncTitle/'
HELIX_ACCEPTED_CHIEF_ADMIN_TITLES = ['FIRE_CHIEF', 'DEPT_CHIEF', 'CEO', 'COMMISH', 'CHIEF_OFF', 'PRES']

STATICSITEMAPS_ROOT_SITEMAP = 'firecares.urls.sitemaps'

CELERY_DEFAULT_QUEUE = "default"
CELERY_DEFAULT_EXCHANGE = "default"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_ROUTING_KEY = "default"
CELERY_CREATE_MISSING_QUEUES = True

CELERY_IMPORTS = (
    'firecares.tasks.cache',
    'firecares.tasks.update',
    'firecares.tasks.email',
    'firecares.tasks.cleanup',
    'firecares.tasks.quality_control',
    'firecares.tasks.slack',
    'firecares.tasks.weather_task',
    'firecares.tasks.predictions'
)

CELERY_QUEUES = [
    Queue('default', routing_key='default'),
    Queue('cache', routing_key='cache'),
    Queue('update', routing_key='update'),
    Queue('email', routing_key='email'),
    Queue('cleanup', routing_key='cleanup'),
    Queue('quality-control', routing_key='quality-control'),
    Queue('slack', routing_key='slack'),
    Queue('servicearea', routing_key='servicearea'),
    Queue('weather-task', routing_key='weather-task'),
    Queue('singlenode', routing_key='singlenode'),
]

ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_OPEN = False
REGISTRATION_FORM = 'firecares.firecares_core.ext.registration.forms.LimitedRegistrationForm'
INVITATIONS_SIGNUP_REDIRECT = 'registration_register'
INVITATIONS_ALLOW_JSON_INVITES = True
INVITATIONS_ACCEPT_INVITE_AFTER_SIGNUP = True
INVITATIONS_GONE_ON_ACCEPT_ERROR = False
INVITATIONS_ADAPTER = 'firecares.firecares_core.ext.invitations.adapters.DepartmentInvitationsAdapter'

EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_PORT = os.getenv('EMAIL_PORT', 25)
EMAIL_SUBJECT_PREFIX = '[FireCARES] '
SERVER_EMAIL = os.getenv('SERVER_EMAIL', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', '')

SLACK_BACKEND = 'django_slack.backends.RequestsBackend'
SLACK_TOKEN = os.getenv('SLACK_TOKEN', None)
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL', '#firecares')
SLACK_ICON_EMOJI = os.getenv('SLACK_ICON_EMOJI', ':goberserk:')
SLACK_USERNAME = os.getenv('SLACK_USERNAME', 'edgebot')
SLACK_FIRECARES_COMMAND_TOKEN = os.getenv('SLACK_FIRECARES_COMMAND_TOKEN', 'edgebot')
DOCUMENT_UPLOAD_BUCKET = os.getenv('DOCUMENT_UPLOAD_BUCKET', 'firecares-uploads')
PHONENUMBER_DB_FORMAT = 'NATIONAL'
PHONENUMBER_DEFAULT_REGION = 'US'
