from django.apps import AppConfig


class PagesConfig(AppConfig):
    """Конфигурация приложения со статическими страницами."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'
