from collections.abc import Callable
from datetime import UTC, datetime

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render

from garimpei.domain.integration.values import IntegrationError, IntegrationView
from garimpei.infra.http.integration.presentation import facebook_context
from garimpei.usecase.integration.configure_whatsapp_usecase import ConfigureWhatsAppUseCase
from garimpei.usecase.integration.confirm_facebook_login_usecase import ConfirmFacebookLoginUseCase
from garimpei.usecase.integration.connect_whatsapp_usecase import ConnectWhatsAppUseCase
from garimpei.usecase.integration.read_facebook_status_usecase import ReadFacebookStatusUseCase
from garimpei.usecase.integration.read_integrations_usecase import ReadIntegrationsUseCase
from garimpei.usecase.integration.read_qr_usecase import ReadWhatsAppQrUseCase
from garimpei.usecase.integration.request_facebook_login_usecase import RequestFacebookLoginUseCase
from garimpei.usecase.integration.save_facebook_usecase import SaveFacebookSessionUseCase


class IntegrationHandler:
    def __init__(
        self,
        read: ReadIntegrationsUseCase,
        save: SaveFacebookSessionUseCase,
        connect: ConnectWhatsAppUseCase,
        configure: ConfigureWhatsAppUseCase,
        qr: ReadWhatsAppQrUseCase,
        disable: Callable[[], None],
        facebook: ReadFacebookStatusUseCase,
        request_login: RequestFacebookLoginUseCase,
        confirm_login: ConfirmFacebookLoginUseCase,
    ) -> None:
        self._request_login, self._confirm_login = request_login, confirm_login
        self._facebook = facebook
        self._read, self._save, self._connect, self._configure, self._qr, self._disable = (
            read,
            save,
            connect,
            configure,
            qr,
            disable,
        )

    def handle(self, request: HttpRequest, action: str = "page") -> HttpResponse:
        if action == "facebook-status":
            if request.method != "GET":
                return HttpResponseNotAllowed(["GET"])
            value = self._facebook.execute()
            return render(
                request,
                "integration/facebook_notice.html",
                facebook_context(value.facebook_phase, detail=request.GET.get("detail") == "1"),
            )
        if action in {"status", "qr"}:
            if request.method != "GET":
                return HttpResponseNotAllowed(["GET"])
            return self._qr_response() if action == "qr" else self._status(request)
        if request.method == "POST":
            return self._post(request)
        if request.method != "GET":
            return HttpResponseNotAllowed(["GET", "POST"])
        view = self._read.execute()
        return render(
            request, "integration/settings.html", context(view, request.GET.get("saved", ""))
        )

    def _post(self, request: HttpRequest) -> HttpResponse:
        action = request.POST.get("action", "")
        if action == "facebook-browser":
            self._request_login.execute()
            return redirect("facebook")
        if action == "facebook-confirm":
            self._confirm_login.execute()
            return redirect("facebook")
        if action == "facebook":
            self._save.execute(request.POST.get("cookies", ""))
            return redirect("facebook")
        if action == "connect":
            self._connect.execute()
            return redirect("whatsapp")
        if action == "whatsapp":
            self._configure.execute(
                request.POST.get("group", ""),
                request.POST.get("account", ""),
                request.POST.get("enabled") == "on",
            )
            return redirect("whatsapp")
        if action == "disable":
            self._disable()
            return redirect("whatsapp")
        raise IntegrationError("Ação inválida. Atualize a página e tente novamente.")

    def _status(self, request: HttpRequest) -> HttpResponse:
        view = self._read.execute(groups=False)
        response = render(request, "integration/whatsapp_status.html", context(view))
        expected = request.GET.get("expected", "")
        if expected and (view.whatsapp.phase == "WORKING") != (expected == "WORKING"):
            # A redirect to the current hash URL can be a no-op in the browser.
            response["HX-Refresh"] = "true"
        return response

    def _qr_response(self) -> HttpResponse:
        response = HttpResponse(self._qr.execute(), content_type="image/png")
        response["X-Content-Type-Options"] = "nosniff"
        return response


def redirect(section: str) -> HttpResponse:
    return HttpResponse(
        status=303, headers={"Location": "/integracoes/?saved=" + section + "#" + section}
    )


def context(view: IntegrationView, saved: str = "") -> dict[str, object]:
    return {
        **facebook_context(view.configuration.facebook_phase, detail=True),
        "account_changed": bool(
            view.whatsapp.phase == "WORKING"
            and view.configuration.whatsapp_configured
            and view.configuration.whatsapp_account != view.whatsapp.account
        ),
        "integration_page": True,
        "integration": view,
        "config": view.configuration,
        "connected": view.whatsapp.phase == "WORKING",
        "pairing": view.whatsapp.phase in {"SCAN_QR_CODE", "STARTING"},
        "qr_ready": view.whatsapp.phase == "SCAN_QR_CODE",
        "qr_version": int(datetime.now(UTC).timestamp()),
        "groups": view.groups,
        "saved": saved if saved in {"facebook", "whatsapp"} else "",
    }
