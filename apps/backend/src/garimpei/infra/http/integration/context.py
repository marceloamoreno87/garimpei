from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.http import HttpRequest

from garimpei.config.env import ConfigurationError
from garimpei.infra.http.integration.presentation import facebook_context
from garimpei.main import build_integration_repository


def integration_context(_request: HttpRequest) -> dict[str, object]:
    try:
        value = build_integration_repository().read()
    except (DatabaseError, ImproperlyConfigured, ConfigurationError):
        return {}
    return facebook_context(value.facebook_phase)
