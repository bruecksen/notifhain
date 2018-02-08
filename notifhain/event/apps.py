from django.apps import AppConfig


class EventConfig(AppConfig):
    name = 'notifhain.event'

    def ready(self):
        import notifhain.event.signals  # noqa
