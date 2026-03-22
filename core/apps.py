from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # השורה הזו היא ה"סטארטר" שמפעיל את ה-Signals
        import core.signals