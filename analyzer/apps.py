from django.apps import AppConfig


class AnalyzerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "analyzer"

    def ready(self):
        """
        Pre-load the FinBERT model when Django starts.
        This means the first request won't pay the model loading cost.
        """
        try:
            from .sentiment import _get_classifier
            _get_classifier()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "FinBERT model could not be pre-loaded: %s", e
            )