from django.http import (
    Http404,
    HttpRequest,
    HttpResponse,
    HttpResponseNotAllowed,
)
from django.shortcuts import render

from garimpei.infra.http.monitoring.forms import parse_input
from garimpei.infra.http.monitoring.presentation import form_context, render_form
from garimpei.usecase.listing.read_collection_status_usecase import ReadCollectionStatusUseCase
from garimpei.usecase.monitoring.complete_configuration_usecase import (
    CompleteMonitoringConfigurationUseCase,
)
from garimpei.usecase.monitoring.preview_products_usecase import PreviewProductsUseCase
from garimpei.usecase.monitoring.read_catalog_usecase import ReadCategoryCatalogUseCase
from garimpei.usecase.monitoring.read_form_usecase import MonitoringForm, ReadMonitoringFormUseCase
from garimpei.usecase.monitoring.save_step_usecase import SaveMonitoringStepUseCase
from garimpei.usecase.monitoring.update_configuration_usecase import (
    UpdateMonitoringConfigurationUseCase,
)
from garimpei.usecase.valuation.read_research_diagnostic_usecase import (
    ReadComparableResearchDiagnosticUseCase,
)


def redirect(destination: str, status: int = 302) -> HttpResponse:
    return HttpResponse(
        status=status, headers={"Location": destination, "Cache-Control": "no-store"}
    )


class MonitoringHandler:
    def __init__(
        self,
        read_form: ReadMonitoringFormUseCase,
        read_catalog: ReadCategoryCatalogUseCase,
        save_step: SaveMonitoringStepUseCase,
        complete: CompleteMonitoringConfigurationUseCase,
        update: UpdateMonitoringConfigurationUseCase,
        preview: PreviewProductsUseCase,
        read_collection_status: ReadCollectionStatusUseCase,
        research: ReadComparableResearchDiagnosticUseCase | None = None,
    ) -> None:
        self._read_form = read_form
        self._read_catalog = read_catalog
        self._save_step = save_step
        self._complete = complete
        self._update = update
        self._preview = preview
        self._read_collection_status = read_collection_status
        self._research = research

    def handle(self, request: HttpRequest, action: str = "root", step: str = "") -> HttpResponse:
        allowed = (
            ["POST"]
            if action == "concluir"
            else ["GET"]
            if action in {"root", "acompanhamento"}
            else ["GET", "POST"]
        )
        if request.method not in allowed:
            return HttpResponseNotAllowed(allowed)
        if action == "etapa" and step not in {"regiao", "custos", "interesses"}:
            raise Http404
        screen = "editar" if action == "editar" else "interesses" if action == "concluir" else step
        catalog = self._read_catalog.execute() if screen in {"interesses", "editar"} else None
        if request.method == "POST":
            # Preserve the submitted form even if PostgreSQL fails before we read the current revision.
            setattr(
                request,
                "monitoring_context",
                form_context(request, MonitoringForm(), screen, catalog),
            )
        state = self._read_form.execute()
        destination = (
            "/acompanhamento/" if state.slot == "active" else f"/configuracao/{state.next_step}/"
        )
        if action == "root":
            return redirect(destination)
        if action in {"editar", "acompanhamento"} and state.slot != "active":
            return redirect(destination)
        if action == "etapa" and state.slot == "active":
            return redirect(destination)
        if action == "etapa" and self._step_blocked(step, state.next_step):
            return redirect(destination)
        if action == "acompanhamento":
            return render(
                request,
                "monitoring/tracking.html",
                {
                    "collection": self._read_collection_status.execute(),
                    "comparable_research": self._research.execute() if self._research else None,
                },
            )
        context = form_context(request, state, screen, catalog)
        setattr(request, "monitoring_context", context)
        if request.method == "GET":
            return render_form(request, context)
        intent = request.POST.get("intent", "")
        if intent == "reload_catalog":
            return render_form(request, context)
        data = parse_input(request, screen)
        if intent == "add" or intent.startswith("remove:"):
            products = self._preview.execute(data.product_names)
            context.update(
                products=products,
                new_product="",
                saved=False,
                preview_message="Produto repetido: mantivemos uma única entrada."
                if len(products) < len(data.product_names)
                else "Interesses ajustados. Salve para confirmar.",
            )
            return render_form(request, context)
        if action == "concluir":
            self._complete.execute(data)
            return redirect("/acompanhamento/", 303)
        if action == "editar":
            self._update.execute(data)
            response = redirect("/configuracoes/", 303)
            response.set_signed_cookie(
                "monitoring_saved",
                "1",
                max_age=30,
                path="/configuracoes/",
                httponly=True,
                samesite="Strict",
            )
            return response
        self._save_step.execute(data)
        next_step = {"regiao": "custos", "custos": "interesses", "interesses": "interesses"}[screen]
        return redirect(f"/configuracao/{next_step}/", 303)

    def _step_blocked(self, requested: str, available: str) -> bool:
        order = ["regiao", "custos", "interesses"]
        return order.index(requested) > order.index(available)
