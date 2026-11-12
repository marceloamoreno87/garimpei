from uuid import UUID

from django.http import HttpRequest, HttpResponse

from garimpei.main import build_identity_handler


def identity_view(request: HttpRequest, identity: UUID) -> HttpResponse:
    return build_identity_handler().handle(request, identity)
