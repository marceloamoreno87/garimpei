from uuid import UUID

from django import forms
from django.http import HttpRequest, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render

from garimpei.domain.assistance.errors import AssistanceError
from garimpei.domain.assistance.ports import AssistanceQueries
from garimpei.domain.assistance.review import ReviewCommand
from garimpei.usecase.assistance.request_review_usecase import RequestReviewUseCase


class ReviewForm(forms.Form):
    purpose = forms.ChoiceField(
        choices=[(name, name) for name in ("identity", "comparables", "condition")]
    )
    expected_revision = forms.IntegerField(min_value=1)
    command_id = forms.UUIDField()


class ExplainForm(forms.Form):
    snapshot_id = forms.UUIDField()
    command_id = forms.UUIDField()


class AssistanceHandler:
    def __init__(self, request: RequestReviewUseCase, queries: AssistanceQueries) -> None:
        self._request, self._queries = request, queries

    def handle(
        self, request: HttpRequest, identity: UUID | None = None, action: str = "read"
    ) -> HttpResponse:
        expected = "POST" if action in {"request", "explain"} else "GET"
        if request.method != expected:
            return HttpResponseNotAllowed([expected])
        if action == "request" and identity is not None:
            ticket = self._listing(request, identity)
            return render(request, "assistance/ticket.html", dict(ticket=ticket), status=202)
        if action == "explain":
            ticket = self._explain(request)
            template = (
                "assistance/feedback.html"
                if request.headers.get("HX-Request") == "true"
                else "assistance/ticket.html"
            )
            return render(request, template, dict(ticket=ticket), status=202)
        if action == "coverage":
            return render(request, "assistance/coverage.html", self._queries.coverage())
        if identity is None:
            raise AssistanceError("not_found", 404)
        return render(request, "assistance/listing.html", self._queries.listing(identity))

    def _listing(self, request: HttpRequest, identity: UUID) -> object:
        form = ReviewForm(request.POST)
        if set(request.POST) - set(form.fields) - {"csrfmiddlewaretoken"} or not form.is_valid():
            raise AssistanceError("invalid_input", 400)
        data = form.cleaned_data
        return self._request.execute(
            ReviewCommand(
                data["command_id"], str(data["purpose"]), identity, int(data["expected_revision"])
            )
        )

    def _explain(self, request: HttpRequest) -> object:
        form = ExplainForm(request.POST)
        if set(request.POST) - set(form.fields) - {"csrfmiddlewaretoken"} or not form.is_valid():
            raise AssistanceError("invalid_input", 400)
        data = form.cleaned_data
        snapshot = self._queries.operations().get("snapshot")
        if snapshot is None or str(getattr(snapshot, "id")) != str(data["snapshot_id"]):
            raise AssistanceError("snapshot_changed", 409)
        return self._request.execute(
            ReviewCommand(
                data["command_id"],
                "operations",
                data["snapshot_id"],
                int(getattr(snapshot, "revision")),
            )
        )
