from uuid import UUID

from django.http import HttpRequest, HttpResponse

from garimpei.main import build_exploration_handler


def condition_view(
    request: HttpRequest, identity: UUID | None = None, action: str = "read"
) -> HttpResponse:
    return build_exploration_handler().handle(request, identity, action)
