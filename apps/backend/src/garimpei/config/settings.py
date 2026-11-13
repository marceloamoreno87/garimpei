from pathlib import Path

from garimpei.config.env import load_config

CONFIG = load_config()
HTTP_DIR = Path(__file__).resolve().parents[1] / "infra/http"
SECRET_KEY = CONFIG.django_secret
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "procrastinate.contrib.django",
    "garimpei.infra.persistence.apps.PersistenceConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "garimpei.infra.http.error_handler.ErrorMiddleware",
]
ROOT_URLCONF = "garimpei.infra.http.urls"
WSGI_APPLICATION = "garimpei.config.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": CONFIG.database,
        "USER": "garimpei",
        "PASSWORD": CONFIG.postgres_password,
        "HOST": "127.0.0.1",
        "PORT": CONFIG.pg_port,
        "OPTIONS": {"connect_timeout": 2, "options": "-c statement_timeout=2000"},
        "TEST": {"NAME": CONFIG.test_database},
    }
}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [HTTP_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "garimpei.infra.http.integration.context.integration_context",
                "garimpei.infra.http.shell_context.shell_context",
            ]
        },
    }
]
STATIC_URL = "/static/"
STATICFILES_DIRS = [HTTP_DIR / "static"]
STATIC_ROOT = CONFIG.directory / "static"
USE_TZ = True
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "UTC"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CSRF_FAILURE_VIEW = "garimpei.infra.http.error_handler.csrf_failure"
PROCRASTINATE_AUTODISCOVER_MODULE_NAME = None
PROCRASTINATE_IMPORT_PATHS: list[str] = []
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"()": "garimpei.infra.runtime.logging.JsonFormatter"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": CONFIG.log_level},
}
