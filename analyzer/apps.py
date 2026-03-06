from django.apps import AppConfig


class AnalyzerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analyzer"

    def ready(self):
        # Don't pre-load model on startup — load lazily on first request
        # This keeps RAM usage low on free hosting (Render 512MB limit)
        pass