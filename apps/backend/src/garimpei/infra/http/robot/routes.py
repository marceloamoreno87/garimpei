from django.http import HttpRequest, HttpResponse

from garimpei.main import build_robot_handler


def robot_view(request: HttpRequest, action: str = "status") -> HttpResponse:
    return build_robot_handler().handle(request, action)
