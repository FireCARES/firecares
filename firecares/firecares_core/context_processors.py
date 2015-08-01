from django.conf import settings


def third_party_tracking_ids(request):
    """
    Retrieve 3rd-party tracking IDs from the settings file and add them to the
    request context.
    """
    return {
        'google_analytics_tracking_id': settings.GOOGLE_ANALYTICS_TRACKING_ID,
    }
