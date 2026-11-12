from django.http import HttpRequest, HttpResponse


def monitoring_view(request: HttpRequest, action: str = "root", step: str = "") -> HttpResponse:
    from garimpei.main import build_monitoring_handler

    return build_monitoring_handler().handle(request, action=action, step=step)
