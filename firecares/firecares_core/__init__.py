from django.apps import AppConfig


default_app_config = 'firecares.firecares_core.CoreConfig'


class CoreConfig(AppConfig):
    name = 'firecares.firecares_core'

    def ready(self):
        import signals  # noqa
