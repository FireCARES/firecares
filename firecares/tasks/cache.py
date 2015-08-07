from celery import task
from django.core.cache import cache
from firecares.firestation.models import FireDepartment


@task(queue='cache')
def cache_histogram_data():
    """
    Adds histogram data to the cache.
    """
    for attr in 'dist_model_score risk_model_deaths risk_model_injuries risk_model_fires_room risk_model_fires_floor' \
                ' risk_model_fires_structure'.split():
        cache.set('all_{0}__count', FireDepartment.get_histogram(attr), timeout=60 * 60 * 24)
