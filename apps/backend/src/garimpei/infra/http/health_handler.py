from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from garimpei.config.env import load_config
from garimpei.main import build_readiness


@require_GET
def health(_request: HttpRequest) -> JsonResponse:
    response = JsonResponse({"status": "alive"})
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def ready(_request: HttpRequest) -> JsonResponse:
    result = build_readiness().execute()
    config = load_config()
    body: dict[str, object] = {
        "status": "ready" if result.ready else "not_ready",
        "environment_id": config.environment_id,
        "run_id": config.run_id,
        "checks": result.checks,
    }
    if not result.ready:
        body["error"] = {"code": "DEPENDENCY_UNAVAILABLE"}
    response = JsonResponse(body, status=200 if result.ready else 503)
    response["Cache-Control"] = "no-store"
    return response
