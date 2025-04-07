from django.apps import AppConfig

class ConnectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'connect'

    def ready(self):
        import connect.signals  # Import signals when app is ready
