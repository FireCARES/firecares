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
