from django.apps import AppConfig


class PersistenceConfig(AppConfig):
    name = "garimpei.infra.persistence"
    label = "runtime"
    default_auto_field = "django.db.models.BigAutoField"
