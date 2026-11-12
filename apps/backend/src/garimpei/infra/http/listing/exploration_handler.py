from collections.abc import Callable
from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render

from garimpei.domain.listing.exploration import Criteria, InvalidExplorationInput
from garimpei.infra.http.listing.condition_handler import ConditionHandler
from garimpei.infra.http.listing.exploration_presentation import detail_context, list_context, url
from garimpei.infra.http.monitoring.monitoring_handler import redirect
from garimpei.usecase.listing.classify_condition_usecase import ClassifyConditionUseCase
from garimpei.usecase.listing.read_collection_status_usecase import ReadCollectionStatusUseCase
from garimpei.usecase.listing.read_condition_usecase import ReadConditionUseCase
from garimpei.usecase.listing.read_exploration_updates_usecase import ReadExplorationUpdatesUseCase
from garimpei.usecase.listing.read_offer_detail_usecase import ReadOfferDetailUseCase
from garimpei.usecase.listing.read_offers_usecase import ReadOffersUseCase
from garimpei.usecase.monitoring.read_configuration_usecase import (
    ReadMonitoringConfigurationUseCase,
)


class ExplorationHandler:
    def __init__(
        self,
        read: ReadOffersUseCase,
        detail: ReadOfferDetailUseCase,
        updates: ReadExplorationUpdatesUseCase,
        condition: ReadConditionUseCase,
        classify: ClassifyConditionUseCase,
        status: ReadCollectionStatusUseCase,
        configuration: ReadMonitoringConfigurationUseCase,
        labels: dict[str, str],
        worker: Callable[[], bool],
    ) -> None:
        self._worker = worker
        self._read, self._detail, self._updates = read, detail, updates
        self._condition, self._classify = condition, classify
        self._status, self._configuration, self._labels = status, configuration, labels

    def handle(
        self, request: HttpRequest, identity: UUID | None = None, action: str = "read"
    ) -> HttpResponse:
        allowed = ["POST"] if action == "classify" else ["GET"]
        if request.method not in allowed:
            return HttpResponseNotAllowed(allowed)
        criteria = Criteria.parse(request.GET)
        if criteria.category and criteria.category not in self._labels:
            raise InvalidExplorationInput(
                f"Categoria {criteria.category!r} inválida: selecione uma categoria do catálogo."
            )
        setattr(request, "exploration_criteria", criteria)
        if action == "updates":
            changed, expired = self._updates.execute(criteria.version)
            return render(
                request,
                "listing/updates.html",
                dict(changed=changed, expired=expired, refresh=url(criteria, version=None)),
            )
        if identity is not None:
            return self._offer(request, identity, criteria, action)
        page = self._read.execute(criteria)
        context = list_context(page, self._labels)
        context.update(
            collection=self._status.execute(),
            configured=self._configuration.execute().configured,
            worker_active=self._worker(),
            applied=request.GET.get("aplicar") == "1",
        )
        template = (
            "listing/results.html"
            if request.headers.get("HX-Request")
            else "listing/exploration.html"
        )
        response = render(request, template, context)
        response["HX-Push-Url"] = str(context["canonical"])
        return response

    def _offer(
        self, request: HttpRequest, identity: UUID, criteria: Criteria, action: str
    ) -> HttpResponse:
        setattr(request, "condition_reader", self._condition)
        setattr(request, "condition_identity", identity)
        current = self._condition.execute(identity)
        if action == "classify":
            return self._save(request, identity, criteria)
        offer, version = self._detail.execute(identity, criteria.version)
        if offer is None:
            raise Http404()
        context = detail_context(offer, criteria.at(version))
        context.update(
            live=current,
            selected_choice=current.state.manual if current else None,
            confirmation=bool(
                current
                and request.get_signed_cookie("condition_saved", default="")
                == f"{identity}:{current.state.revision}"
            ),
            applied=request.GET.get("aplicar") == "1",
        )
        response = render(request, "listing/offer_detail.html", context)
        response["HX-Push-Url"] = url(criteria.at(version), f"/ofertas/{identity}/")
        response.delete_cookie("condition_saved", path=f"/ofertas/{identity}/")
        return response

    def _save(self, request: HttpRequest, identity: UUID, criteria: Criteria) -> HttpResponse:
        if request.GET:
            offer, version = self._detail.execute(identity, criteria.version)
            if offer:
                setattr(
                    request,
                    "exploration_detail_context",
                    detail_context(offer, criteria.at(version)),
                )
        choice, revision = ConditionHandler._input(request)
        updated = self._classify.execute(identity, choice, revision)
        target = url(criteria, f"/ofertas/{identity}/") if request.GET else f"/ofertas/{identity}/"
        response = redirect(target, 303)
        response.set_signed_cookie(
            "condition_saved",
            f"{identity}:{updated}",
            max_age=30,
            path=f"/ofertas/{identity}/",
            httponly=True,
            samesite="Strict",
        )
        return response
