"""Route-based orientation shared by full pages, including recoverable errors."""

from django.http import HttpRequest


def shell_context(request: HttpRequest) -> dict[str, str]:
    route = request.resolver_match.url_name if request.resolver_match else ""
    route = route or ""
    if route.startswith(("condition-", "exploration-", "identity-", "media-")):
        return {"ui_page": "offers", "ui_label": "Ofertas"}
    if route == "navigation-suggestions":
        return {"ui_page": "suggestions", "ui_label": "Sugestões relacionadas"}
    if route.startswith(("operations-", "navigation-")) or route == "monitoring-tracking":
        return {"ui_page": "tracking", "ui_label": "Acompanhamento"}
    if route.startswith("inference-"):
        return {"ui_page": "ai", "ui_label": "IA local"}
    if route.startswith("integration-"):
        return {"ui_page": "integrations", "ui_label": "Integrações"}
    return {"ui_page": "settings", "ui_label": "Configurações"}
