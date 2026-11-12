import logging
from collections.abc import Callable

from django.db import DatabaseError
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.integration.values import IntegrationError
from garimpei.domain.listing.condition_ports import ConditionError
from garimpei.domain.listing.exploration import Criteria, ExplorationError
from garimpei.domain.monitoring.errors import (
    ConfigurationReadFailed,
    ConfigurationSaveFailed,
    MonitoringError,
)
from garimpei.infra.http.listing.condition_presentation import condition_error
from garimpei.infra.http.listing.exploration_presentation import url
from garimpei.infra.http.monitoring.presentation import error_response
from garimpei.usecase.listing.read_condition_usecase import ReadConditionUseCase


class ErrorMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self._get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.get_host()
        response = self._get_response(request)
        if request.path.startswith("/integracoes/"):
            response["Cache-Control"] = "no-store"
            response["Cross-Origin-Resource-Policy"] = "same-origin"
            response["X-Frame-Options"] = "DENY"
            response["Referrer-Policy"] = "same-origin"
        return response

    def process_exception(
        self, _request: HttpRequest, _exception: Exception
    ) -> HttpResponse | None:
        if _request.path.startswith("/integracoes/ia/") and isinstance(
            _exception, (InferenceError, DatabaseError)
        ):
            status = _exception.status if isinstance(_exception, InferenceError) else 503
            message = "Não foi possível gravar ou ler o estado da IA. Tente novamente."
            if status == 409:
                message = (
                    "O estado mudou em outra janela. Confira o estado atual e tente novamente."
                )
            if status == 400:
                message = "Revisão inválida. Reabra o estado da IA antes de enviar a ação."
            return render(
                _request,
                "inference/error.html",
                {"integration_page": True, "message": message},
                status=status,
            )
        if isinstance(_exception, IntegrationError):
            response = render(
                _request,
                "integration/error.html",
                {"integration_page": True, "error": _exception},
                status=_exception.status,
            )
            response["Cache-Control"] = "no-store"
            return response
        if isinstance(_exception, ExplorationError):
            criteria: Criteria = getattr(_request, "exploration_criteria", Criteria())
            response = render(
                _request,
                "listing/exploration_error.html",
                dict(
                    message=_exception.message,
                    refresh=url(criteria, version=None),
                    listing_page=True,
                ),
                status=_exception.status,
            )
            response["HX-Retarget"] = "#exploration-feedback"
            response["HX-Reswap"] = "innerHTML"
            return response
        if isinstance(_exception, ConditionError):
            logging.getLogger("garimpei.http").warning(
                _exception.code,
                extra={"event": "condition_error", "error_code": _exception.code},
            )
            reader: ReadConditionUseCase | None = getattr(_request, "condition_reader", None)
            if reader is not None:
                return condition_error(_request, _exception, reader)
        if isinstance(_exception, Http404):
            return None
        if isinstance(_exception, ConfigurationReadFailed) and _request.method == "POST":
            _exception = ConfigurationSaveFailed()
        if isinstance(_exception, MonitoringError):
            logging.getLogger("garimpei.http").warning(
                _exception.code,
                extra={"event": "configuration_error", "error_code": _exception.code},
            )
            return error_response(_request, _exception)
        logging.getLogger("garimpei.http").error(
            "HTTP_ERROR", extra={"event": "http_error", "error_code": "INTERNAL_ERROR"}
        )
        route = _request.resolver_match
        if route is not None and (route.url_name or "").startswith("monitoring-"):
            return render(_request, "monitoring/error.html", status=500)
        return JsonResponse({"error": {"code": "INTERNAL_ERROR"}}, status=500)


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    del reason  # Django passes an internal explanation; do not disclose it in the response or logs.
    return render(request, "monitoring/csrf_error.html", status=403)
