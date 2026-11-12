from typing import cast

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from garimpei.domain.monitoring.errors import MonitoringError
from garimpei.domain.monitoring.values import CategoryCatalog
from garimpei.domain.navigation.read_models import SuggestionView
from garimpei.usecase.monitoring.read_form_usecase import MonitoringForm


def form_context(
    request: HttpRequest, state: MonitoringForm, step: str, catalog: CategoryCatalog | None
) -> dict[str, object]:
    editing = step == "editar"
    form_url = (
        reverse("monitoring-edit") if editing else reverse("monitoring-step", kwargs={"step": step})
    )
    context: dict[str, object] = {
        "step": step,
        "editing": editing,
        "form_url": form_url,
        "revision": state.revision,
        "cep": state.cep,
        "shipping_estimate": state.shipping_estimate,
        "resale_fee_percent": state.resale_fee_percent,
        "products": [item.label for item in state.interests if item.kind == "product"],
        "selected": [item.key for item in state.interests if item.kind == "category"],
        "catalog": catalog,
        "categories": category_options(state, catalog),
        "saved": editing
        and request.method == "GET"
        and request.get_signed_cookie("monitoring_saved", default="", max_age=30) == "1",
        "error": None,
    }
    suggestion: SuggestionView | None = getattr(request, "navigation_suggestion", None)
    if editing and request.method == "GET" and suggestion is not None:
        products = [item.label for item in state.interests if item.kind == "product"]
        context["products"] = list(dict.fromkeys([*products, suggestion.term]))
        context["preview_message"] = (
            "Proposta editável. Salve as configurações para iniciar o monitoramento."
        )
        context["saved"] = False
    if request.method == "POST":
        preserve_input(request, context, step)
    return context


def category_options(
    state: MonitoringForm, catalog: CategoryCatalog | None
) -> list[dict[str, object]]:
    selected = {item.key for item in state.interests if item.kind == "category"}
    entries = (
        []
        if catalog is None
        else [
            {
                "id": item.id,
                "label": catalog.path(item),
                "selectable": item.selectable or item.id in selected,
                "retired": not item.selectable and item.id in selected,
                "source_url": item.source_url,
            }
            for item in catalog.entries
        ]
    )
    known = {item["id"] for item in entries}
    entries.extend(
        [
            {"id": item.key, "label": item.label, "selectable": True, "retired": True}
            for item in state.interests
            if item.kind == "category" and item.key not in known
        ]
    )
    return entries


def preserve_input(request: HttpRequest, context: dict[str, object], step: str) -> None:
    fields = (
        ["cep", "shipping_estimate", "resale_fee_percent"]
        if step == "editar"
        else {"regiao": ["cep"], "custos": ["shipping_estimate", "resale_fee_percent"]}.get(
            step, []
        )
    )
    for field in fields:
        context[field] = request.POST.get(field, "")
    context["revision"] = request.POST.get("revision", "")
    if step in {"interesses", "editar"}:
        context["products"] = request.POST.getlist("product_names[]")
        context["selected"] = request.POST.getlist("category_ids[]")
        context["new_product"] = request.POST.get("new_product", "")


def render_form(
    request: HttpRequest, context: dict[str, object], status: int = 200
) -> HttpResponse:
    response = render(request, "monitoring/form.html", context, status=status)
    response["Cache-Control"] = "no-store"
    if context.get("saved"):
        response.delete_cookie("monitoring_saved", path="/configuracoes/", samesite="Strict")
    if status >= 400 and request.headers.get("HX-Request") == "true":
        response["HX-Replace-Url"] = str(context["form_url"])
    return response


def error_response(request: HttpRequest, error: MonitoringError) -> HttpResponse:
    context = cast(dict[str, object] | None, getattr(request, "monitoring_context", None))
    if context is None:
        return render(request, "monitoring/error.html", {"error": error}, status=error.status)
    context["error"] = error
    return render_form(request, context, status=error.status)
