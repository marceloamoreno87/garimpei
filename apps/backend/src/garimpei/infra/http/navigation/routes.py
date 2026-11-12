from django.http import HttpRequest, HttpResponse


def navigation_view(request: HttpRequest, action: str = "status") -> HttpResponse:
    from garimpei.main import build_navigation_handler

    return build_navigation_handler().handle(request, action)
