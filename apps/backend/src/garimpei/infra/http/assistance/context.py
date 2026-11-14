from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.http import HttpRequest

from garimpei.main import build_assistance_queries


def assistance_context(request: HttpRequest) -> dict[str, object]:
    if request.path not in {"/acompanhamento/", "/acompanhamento/estado/"}:
        return {}
    try:
        return {"assistance_operations": build_assistance_queries().operations()}
    except (DatabaseError, ImproperlyConfigured):
        return {"assistance_operations": {"unavailable": True}}
