from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from garimpei.domain.listing.condition import Tab
from garimpei.domain.listing.condition_ports import ConditionError, ConditionView
from garimpei.usecase.listing.read_condition_usecase import ReadConditionUseCase

TABS: tuple[tuple[Tab, str], ...] = (
    ("funcionam", "Funcionam bem"),
    ("defeitos", "Com defeito"),
    ("incerta", "Condição não confirmada"),
)
MESSAGES = {
    "CONDITION_CONFLICT": "Esta oferta mudou. Revise a classificação atual antes de salvar novamente.",
    "INVALID_CONDITION_INPUT": "Escolha Funciona bem ou Não funciona bem e use a revisão atual do formulário.",
    "CONDITION_SAVE_FAILED": "Não foi possível salvar sua classificação. A escolha confirmada foi mantida. Tente novamente.",
    "CONDITION_NOT_FOUND": "Esta oferta não foi encontrada.",
    "CONDITION_UNAVAILABLE": "Não foi possível consultar as ofertas. Recarregue para tentar novamente.",
}


def detail_context(request: HttpRequest, view: ConditionView | None) -> dict[str, object]:
    state = view.state if view else None
    fields = {"title": "Título", "description": "Descrição", "condition": "Condição informada"}
    return {
        "listing_page": True,
        "offer": view,
        "selected_choice": request.POST.get("choice", "")
        if request.method == "POST"
        else state.manual
        if state
        else None,
        "signals": tuple((fields[signal.field], signal.text) for signal in state.analysis.signals)
        if state
        else (),
        "automatic_label": {
            "good": "Funcionam bem",
            "defect": "Com defeito",
            "uncertain": "Condição não confirmada",
        }[state.analysis.condition]
        if state
        else "",
        "confirmation": bool(
            view
            and state
            and request.get_signed_cookie("condition_saved", default="")
            == f"{view.id}:{state.revision}"
        ),
    }


def condition_error(
    request: HttpRequest, error: ConditionError, reader: ReadConditionUseCase
) -> HttpResponse:
    identity: UUID | None = getattr(request, "condition_identity", None)
    view = None
    readable = True
    try:
        view = reader.execute(identity) if identity else None
    except ConditionError:
        readable = False
    context = detail_context(request, view)
    context.update(
        error=MESSAGES[error.code],
        error_code=error.code,
        readable=readable,
        submitted=bool(request.POST),
        reload_url=f"/ofertas/{identity}/" if identity else "/ofertas/",
    )
    exploration: dict[str, object] | None = getattr(request, "exploration_detail_context", None)
    if exploration is not None:
        exploration.update(
            error=MESSAGES[error.code],
            error_code=error.code,
            live=view,
            selected_choice=request.POST.get("choice", ""),
            readable=readable,
            submitted=bool(request.POST),
        )
        return render(request, "listing/offer_detail.html", exploration, status=error.status)
    return render(request, "listing/detail.html", context, status=error.status)
