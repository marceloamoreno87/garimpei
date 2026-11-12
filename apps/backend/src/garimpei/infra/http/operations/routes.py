from uuid import UUID

from django.http import HttpRequest, HttpResponseBase


def operations_view(
    request: HttpRequest, action: str = "status", stage: str = "", identity: UUID | None = None
) -> HttpResponseBase:
    from garimpei.main import build_operations_handler

    return build_operations_handler().handle(request, action=action, stage=stage, identity=identity)
