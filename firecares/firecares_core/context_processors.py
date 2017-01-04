from django.conf import settings
from django.core.cache import cache
from django.db.models import Max, Min
from firecares.firestation.models import FireDepartment


def global_settings(request):
    """
    Expose various settings
    """
    return {
        'global_settings': {
            'google_analytics_tracking_id': settings.GOOGLE_ANALYTICS_TRACKING_ID,
            'IMIS_SSO_LOGIN_URL': settings.IMIS_SSO_LOGIN_URL,
            'HELIX_LOGOUT_URL': settings.HELIX_LOGOUT_URL
        }
    }


def fire_department_search(request):
    """
    Required context variables for fire department search.
    """
    context = cache.get('fire_department_search_context')
    if context:
        return context

    score_metrics = FireDepartment.objects.filter(archived=False).aggregate(
        Max('firedepartmentriskmodels__dist_model_score'),
        Min('firedepartmentriskmodels__dist_model_score'),
        Max('population'),
        Min('population'),
    )

    context = {
        'dist_max': score_metrics['firedepartmentriskmodels__dist_model_score__max'],
        'dist_min': score_metrics['firedepartmentriskmodels__dist_model_score__min'],
        'population_max': score_metrics['population__max'] or 0,
        'population_min': score_metrics['population__min'] or 0,
    }

    cache.set('fire_department_search_context', context, 60 * 60 * 24)

    return context
