import re
from uuid import UUID

from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render

from garimpei.domain.listing.condition import Choice, Tab
from garimpei.domain.listing.condition_ports import InvalidConditionInput
from garimpei.infra.http.listing.condition_presentation import TABS, detail_context
from garimpei.infra.http.monitoring.monitoring_handler import redirect
from garimpei.usecase.listing.classify_condition_usecase import ClassifyConditionUseCase
from garimpei.usecase.listing.list_conditions_usecase import ListConditionsUseCase
from garimpei.usecase.listing.read_condition_usecase import ReadConditionUseCase


class ConditionHandler:
    def __init__(
        self,
        read: ReadConditionUseCase,
        listing: ListConditionsUseCase,
        classify: ClassifyConditionUseCase,
    ) -> None:
        self._read = read
        self._listing = listing
        self._classify = classify

    def handle(
        self, request: HttpRequest, identity: UUID | None = None, action: str = "read"
    ) -> HttpResponse:
        setattr(request, "condition_reader", self._read)
        setattr(request, "condition_identity", identity)
        allowed = ["POST"] if action == "classify" else ["GET"]
        if request.method not in allowed:
            return HttpResponseNotAllowed(allowed)
        if identity is None:
            return self._list(request)
        if action == "classify":
            choice, revision = self._input(request)
            updated = self._classify.execute(identity, choice, revision)
            response = redirect(f"/ofertas/{identity}/", 303)
            response.set_signed_cookie(
                "condition_saved",
                f"{identity}:{updated}",
                max_age=30,
                path=f"/ofertas/{identity}/",
                httponly=True,
                samesite="Strict",
            )
            return response
        view = self._read.execute(identity)
        response = render(request, "listing/detail.html", detail_context(request, view))
        response.delete_cookie("condition_saved", path=f"/ofertas/{identity}/")
        return response

    def _list(self, request: HttpRequest) -> HttpResponse:
        value = request.GET.get("aba", "funcionam")
        if value not in {tab for tab, _ in TABS}:
            raise InvalidConditionInput()
        tab: Tab = (
            "funcionam"
            if value == "funcionam"
            else "defeitos"
            if value == "defeitos"
            else "incerta"
        )
        # Each read is internally consistent; a single population supplies all tab counts.
        offers = self._listing.execute(tab)
        return render(
            request,
            "listing/list.html",
            {"listing_page": True, "offers": offers, "tab": tab, "tabs": TABS},
        )

    @staticmethod
    def _input(request: HttpRequest) -> tuple[Choice, int]:
        choice, revision = request.POST.get("choice", ""), request.POST.get("revision", "")
        if choice not in {"good", "defect"} or not re.fullmatch(r"[0-9]{1,18}", revision):
            raise InvalidConditionInput()
        return ("good" if choice == "good" else "defect"), int(revision)
