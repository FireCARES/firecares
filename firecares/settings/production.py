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
