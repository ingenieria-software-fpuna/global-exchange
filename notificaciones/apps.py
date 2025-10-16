from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notificaciones'
    verbose_name = 'Notificaciones'

    def ready(self):
        """
        Importa las señales cuando la app está lista
        """
        import notificaciones.signals  # noqa: F401
