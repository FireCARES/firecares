from django.conf import settings
from firecares.firestation.models import FireDepartment, Max, Min


def third_party_tracking_ids(request):
    """
    Retrieve 3rd-party tracking IDs from the settings file and add them to the
    request context.
    """
    return {
        'google_analytics_tracking_id': settings.GOOGLE_ANALYTICS_TRACKING_ID,
    }


def fire_department_search(request):
    """
    Required context variables for fire department search.
    """
    context = {}
    score_metrics = FireDepartment.objects.all().aggregate(Max('dist_model_score'), Min('dist_model_score'))
    context['dist_max'] = score_metrics['dist_model_score__max']
    context['dist_min'] = score_metrics['dist_model_score__min']

    population_metrics = FireDepartment.objects.all().aggregate(Max('population'), Min('population'))
    context['population_max'] = population_metrics['population__max'] or 0
    context['population_min'] = population_metrics['population__min'] or 0

    return context
