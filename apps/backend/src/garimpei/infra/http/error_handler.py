import logging
from collections.abc import Callable

from django.db import DatabaseError
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.integration.values import IntegrationError
from garimpei.domain.listing.condition_ports import ConditionError
from garimpei.domain.listing.exploration import Criteria, ExplorationError
from garimpei.domain.media.errors import MediaError
from garimpei.domain.monitoring.errors import (
    ConfigurationReadFailed,
    ConfigurationSaveFailed,
    MonitoringError,
)
from garimpei.domain.navigation.ports import NavigationError
from garimpei.domain.operations.errors import OperationsError
from garimpei.domain.robot.errors import RobotError
from garimpei.domain.valuation.identity_errors import IdentityError
from garimpei.infra.http.listing.condition_presentation import condition_error
from garimpei.infra.http.listing.exploration_presentation import url
from garimpei.infra.http.monitoring.presentation import error_response
from garimpei.infra.http.valuation.identity_forms import IdentityForm
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
        if _request.path.startswith("/acompanhamento/robo/") and isinstance(
            _exception, (RobotError, DatabaseError, ValueError)
        ):
            status = (
                _exception.status
                if isinstance(_exception, RobotError)
                else 400
                if isinstance(_exception, ValueError)
                else 503
            )
            message = (
                _exception.message
                if isinstance(_exception, RobotError)
                else "Comando inválido: esperado UUID canônico."
                if status == 400
                else "Não foi possível consultar ou gravar o controle do robô. Tente novamente."
            )
            response = render(_request, "robot/error.html", {"message": message}, status=status)
            response["Cache-Control"] = "no-store"
            return response
        operational_route = _request.path == "/acompanhamento/" or _request.path.startswith(
            (
                "/acompanhamento/estado/",
                "/acompanhamento/etapas/",
                "/acompanhamento/backups/",
                "/acompanhamento/exportacoes/",
            )
        )
        if operational_route and isinstance(
            _exception, (OperationsError, DatabaseError, ConfigurationReadFailed)
        ):
            return operational_error(_request, _exception)

        if isinstance(_exception, IdentityError) or (
            _request.path.endswith("/identidade/") and isinstance(_exception, DatabaseError)
        ):
            response = render(
                _request,
                "valuation/identity_error.html",
                {
                    "message": _exception.message
                    if isinstance(_exception, IdentityError)
                    else "Não foi possível gravar a identidade. Sua entrada continua disponível para tentar novamente.",
                    "identity_form": IdentityForm(_request.POST),
                    "resolution": _request.POST.get("resolution", ""),
                    "request_path": _request.get_full_path(),
                    "return_path": _request.path.removesuffix("identidade/")
                    + ("?" + _request.GET.urlencode() if _request.GET else ""),
                },
                status=_exception.status if isinstance(_exception, IdentityError) else 503,
            )
            response["Cache-Control"] = "no-store"
            return response
        if isinstance(_exception, MediaError):
            media_response = JsonResponse({"code": _exception.code}, status=_exception.status)
            media_response["Cache-Control"] = "private, no-cache"
            return media_response
        navigation_route = _request.path.startswith(
            ("/acompanhamento/navegacao/", "/sugestoes/")
        ) or (_request.path == "/configuracoes/" and "sugestao" in _request.GET)
        if isinstance(_exception, NavigationError) or (
            navigation_route and isinstance(_exception, DatabaseError)
        ):
            response = render(
                _request,
                "navigation/error.html",
                {
                    "message": _exception.message
                    if isinstance(_exception, NavigationError)
                    else "Não foi possível ler ou gravar o percurso. Tente novamente."
                },
                status=_exception.status if isinstance(_exception, NavigationError) else 503,
            )
            response["HX-Retarget"] = "#navigation-feedback"
            response["HX-Reswap"] = "innerHTML"
            response["Cache-Control"] = "no-store"
            return response
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


def operational_error(request: HttpRequest, error: Exception) -> HttpResponse:
    code = error.code if isinstance(error, OperationsError) else "OPERATIONS_UNAVAILABLE"
    status = error.status if isinstance(error, OperationsError) else 503
    message = "Não foi possível concluir a operação. Os dados confirmados continuam preservados."
    if code == "recovery_barrier":
        message = "O despacho permanece bloqueado até reconciliar o intervalo após a cópia."
    if code == "operational_revision_conflict":
        message = "O estado mudou. Reabra o acompanhamento e use a revisão atual antes de retomar."
    if code == "operational_access_suspended":
        message = (
            "O acesso à fonte continua suspenso. Recupere o acesso em Integrações antes de retomar."
        )
    response: HttpResponse
    if request.path.endswith("/estado/") and request.GET.get("formato") != "html":
        response = JsonResponse(
            {"error": {"code": code, "message": message}, "retry_url": request.get_full_path()},
            status=status,
        )
    else:
        template = (
            "operations/feedback.html"
            if request.headers.get("HX-Request") == "true"
            else "operations/error.html"
        )
        response = render(
            request,
            template,
            {"message": message, "retry_url": request.get_full_path()},
            status=status,
        )
    response["Cache-Control"] = "no-store"
    response["HX-Retarget"] = "#operational-feedback"
    response["HX-Reswap"] = "innerHTML"
    return response
