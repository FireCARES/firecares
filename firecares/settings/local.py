from firecares.settings.base import *  # noqa

INSTALLED_APPS += ('debug_toolbar', 'fixture_magic', 'django_extensions')  # noqa
MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware', )  # noqa

# The Django Debug Toolbar will only be shown to these client IPs.
INTERNAL_IPS = (
    '127.0.0.1',
)

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TEMPLATE_CONTEXT': True,
    'HIDE_DJANGO_SQL': False,
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'magic'
    }
}

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

LOGGING['loggers'] = {  # noqa
    'django.request': {
        'handlers': ['mail_admins'],
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
}


def show_toolbar(request):
    return False


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": show_toolbar,
}

TASTYPIE_FULL_DEBUG = True

# EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CELERY_ALWAYS_EAGER = True

REGISTRATION_OPEN = True
STATICSITEMAPS_USE_GZIP = False
STATICSITEMAPS_ROOT_DIR = '/tmp/sitemaps'

try:
    from local_settings import *  # noqa
except ImportError:
    pass
