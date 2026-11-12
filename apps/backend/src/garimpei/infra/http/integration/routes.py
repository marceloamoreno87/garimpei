from django.http import HttpRequest, HttpResponse

from garimpei.main import build_integration_handler


def integration_view(request: HttpRequest, action: str = "page") -> HttpResponse:
    response = build_integration_handler().handle(request, action)
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "same-origin"
    response["Cross-Origin-Resource-Policy"] = "same-origin"
    response["X-Frame-Options"] = "DENY"
    return response
