"""Importable without secrets, a database connection or side effects."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
HTTP_DIR = Path(__file__).resolve().parents[1] / "infra/http"
SECRET_KEY = "isolated-test-settings-not-for-runtime"
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "procrastinate.contrib.django",
    "garimpei.infra.persistence.apps.PersistenceConfig",
]
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "garimpei.infra.http.error_handler.ErrorMiddleware",
]
ROOT_URLCONF = "garimpei.infra.http.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [HTTP_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": ["garimpei.infra.http.integration.context.integration_context"]
        },
    }
]
STATIC_URL = "/static/"
STATICFILES_DIRS = [HTTP_DIR / "static"]
STATIC_ROOT = BASE_DIR / ".test-static"
USE_TZ = True
LANGUAGE_CODE = "pt-br"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CSRF_FAILURE_VIEW = "garimpei.infra.http.error_handler.csrf_failure"
PROCRASTINATE_AUTODISCOVER_MODULE_NAME = None
PROCRASTINATE_IMPORT_PATHS: list[str] = []
