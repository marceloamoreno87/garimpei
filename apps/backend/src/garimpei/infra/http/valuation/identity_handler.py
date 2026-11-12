from typing import Literal, cast
from uuid import UUID

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed

from garimpei.domain.listing.exploration import Criteria
from garimpei.domain.valuation.identity_errors import InvalidIdentityInput
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.domain.valuation.product_catalog import ALLOWED
from garimpei.infra.http.listing.exploration_presentation import url
from garimpei.infra.http.valuation.identity_forms import IdentityForm
from garimpei.usecase.valuation.save_identity_usecase import SaveIdentityUseCase


class IdentityHandler:
    def __init__(self, save: SaveIdentityUseCase) -> None:
        self._save = save

    def handle(self, request: HttpRequest, identity: UUID) -> HttpResponse:
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        form = IdentityForm(request.POST)
        if set(request.POST) - set(form.fields) - {"csrfmiddlewaretoken"} or not form.is_valid():
            raise InvalidIdentityInput()
        criteria = Criteria.parse(request.GET)
        data = form.cleaned_data
        self._save.execute(
            IdentityEdit(
                identity,
                int(data["observed_revision"]),
                int(data["manual_revision"]),
                cast(Literal["save", "resolve"], data["action"]),
                tuple((name, str(data[name])) for name in ALLOWED if data.get(name)),
                cast(
                    Literal["keep_manual", "use_observed", "correct"] | None,
                    data.get("resolution") or None,
                ),
            )
        )
        destination = url(criteria, f"/ofertas/{identity}/") + "&identidade=salva"
        return HttpResponse(
            status=303, headers={"Location": destination, "Cache-Control": "no-store"}
        )
