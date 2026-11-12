from django.http import HttpRequest, HttpResponse


def monitoring_view(request: HttpRequest, action: str = "root", step: str = "") -> HttpResponse:
    from garimpei.main import build_monitoring_handler

    if action == "editar" and request.method == "GET" and request.GET.get("sugestao"):
        from garimpei.infra.http.navigation.navigation_handler import parse_identity
        from garimpei.main import build_read_suggestion

        suggestion = build_read_suggestion().execute(parse_identity(request.GET["sugestao"]))
        setattr(request, "navigation_suggestion", suggestion)
    return build_monitoring_handler().handle(request, action=action, step=step)
