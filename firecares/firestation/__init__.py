from django.apps import AppConfig
from django.db.models.signals import post_migrate

default_app_config = 'firecares.firestation.FireStationAppConfig'


class FireStationAppConfig(AppConfig):
    name = 'firecares.firestation'

    def ready(self):
        from .models import create_quartile_views
        post_migrate.connect(create_quartile_views, sender=self)
