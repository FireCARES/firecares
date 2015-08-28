from firecares.celery import app
from django.core.cache import cache
from firecares.firestation.models import FireDepartment


@app.task(queue='cache')
def cache_histogram_data():
    """
    Adds histogram data to the cache.
    """
    for attr in 'dist_model_score risk_model_deaths risk_model_injuries risk_model_fires_size0 risk_model_fires_size1' \
                ' risk_model_fires_size2 risk_model_fires'.split():
        cache.set('all_{0}__count', FireDepartment.get_histogram(attr), timeout=60 * 60 * 24)
