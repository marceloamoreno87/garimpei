from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_protect

from garimpei.main import build_media_handler


@csrf_protect
def media_view(
    request: HttpRequest, identity: UUID, version: UUID | None = None, variant: str = ""
) -> HttpResponse:
    return build_media_handler().handle(request, identity, version, variant)
