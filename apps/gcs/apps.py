from django.apps import AppConfig


class GcsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.gcs'
    verbose_name = 'Google Cloud Storage' 