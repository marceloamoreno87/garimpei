import json
from collections.abc import Callable
from dataclasses import asdict
from typing import cast
from uuid import UUID

from django.db import transaction
from django.db.models import Max
from django.utils.timezone import now

from garimpei.domain.assistance.errors import AssistanceError
from garimpei.domain.assistance.review import PROFILES, ReviewCommand, ReviewTicket
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.request import AnalysisInput
from garimpei.infra.gateway.assistance.snapshots import (
    digest,
    interest_snapshot,
    observation_snapshot,
    operations_snapshot,
)
from garimpei.infra.persistence.assistance_models import (
    AssistanceCommand,
    AssistanceOperationsSnapshot,
    AssistancePolicy,
    AssistanceReview,
    AssistanceReviewRequest,
)
from garimpei.infra.persistence.inference_models import InferenceControl
from garimpei.infra.persistence.listing_models import Listing, ListingObservation
from garimpei.infra.persistence.monitoring_models import MonitoringInterest
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
from garimpei.infra.repository.assistance.publication import current_review, publish_review
from garimpei.infra.repository.robot.postgres_repository import robot_enabled
from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase


class PostgresAssistanceRepository:
    def __init__(
        self, request: RequestAnalysisUseCase, condition_request: Callable[[], int] | None = None
    ) -> None:
        self._request, self._condition_request = request, condition_request

    @transaction.atomic
    def admit(self, command: ReviewCommand) -> ReviewTicket:
        lock_monitoring_publication()
        command_hash = digest(asdict(command))
        previous = (
            AssistanceCommand.objects.select_related("review").filter(id=command.command_id).first()
        )
        if previous:
            if previous.command_hash != command_hash:
                raise AssistanceError("command_conflict", 409)
            return _ticket(previous.review, True)
        if command.purpose == "operations":
            review = self._operations(command)
        else:
            review = self._listing(command)
        AssistanceCommand.objects.create(
            id=command.command_id, command_hash=command_hash, review=review
        )
        return _ticket(review, review.cache_reuses > 0)

    def _listing(self, command: ReviewCommand) -> AssistanceReview:
        row = (
            Listing.objects.select_related("latest", "identity_progress__manual__observation")
            .filter(id=command.target_id)
            .first()
        )
        if row is None or row.latest is None:
            raise AssistanceError("not_found", 404)
        if row.latest.ordinal != command.expected_revision:
            raise AssistanceError("revision_conflict", 409)
        if command.purpose not in {"identity", "comparables", "condition"}:
            raise AssistanceError("invalid_input", 400)
        candidate = (
            self._candidates(row)[0]
            if command.purpose == "comparables" and self._candidates(row)
            else None
        )
        if command.purpose == "comparables" and candidate is None:
            raise AssistanceError("insufficient_input")
        return self._create(
            command.purpose,
            "listing_observation",
            row.latest.id,
            row.latest.ordinal,
            observation_snapshot(row, command.purpose, candidate),
            row.latest,
            candidate,
        )

    def _operations(self, command: ReviewCommand) -> AssistanceReview:
        snapshot = AssistanceOperationsSnapshot.objects.filter(id=command.target_id).first()
        if snapshot is None:
            raise AssistanceError("not_found", 404)
        if (
            snapshot != AssistanceOperationsSnapshot.objects.order_by("-revision").first()
            or snapshot.revision != command.expected_revision
        ):
            raise AssistanceError("snapshot_changed", 409)
        return self._create(
            "operations",
            "operations_snapshot",
            snapshot.id,
            snapshot.revision,
            operations_snapshot(snapshot),
            operations=snapshot,
        )

    def _create(
        self,
        purpose: str,
        kind: str,
        identity: UUID,
        revision: int,
        snapshot: dict[str, object],
        observation: ListingObservation | None = None,
        candidate: ListingObservation | None = None,
        operations: AssistanceOperationsSnapshot | None = None,
    ) -> AssistanceReview:
        signature = digest(snapshot)
        previous = AssistanceReview.objects.filter(
            purpose=purpose, target_kind=kind, target_id=identity, input_signature=signature
        ).first()
        if previous:
            previous.cache_reuses += 1
            previous.save(update_fields=["cache_reuses"])
            return previous
        generation = (
            AssistanceReview.objects.filter(
                purpose=purpose, target_kind=kind, target_id=identity
            ).aggregate(value=Max("generation"))["value"]
            or 0
        ) + 1
        row = AssistanceReview.objects.create(
            purpose=purpose,
            target_kind=kind,
            target_id=identity,
            observation=observation,
            candidate_observation=candidate,
            operations_snapshot=operations,
            input_signature=signature,
            generation=generation,
            input_snapshot=json.loads(json.dumps(snapshot, default=str)),
        )
        if purpose != "condition":
            self._submit(row, revision)
        elif self._condition_request is not None:
            transaction.on_commit(self._condition_request)
        return row

    def _submit(self, row: AssistanceReview, revision: int) -> None:
        ticket = self._request.execute(
            AnalysisInput(
                row.observation_id,
                revision,
                json.dumps(row.input_snapshot, ensure_ascii=False, sort_keys=True),
                (),
                PROFILES[row.purpose],
                PROFILES[row.purpose],
                target_kind=row.target_kind,
                target_id=row.target_id,
                target_revision=revision,
                context=dict(
                    policy=str(row.input_snapshot["policy"]),
                    signature=row.input_signature,
                    candidate_id=str(row.candidate_observation_id)
                    if row.candidate_observation_id
                    else None,
                    candidate_revision=row.input_snapshot.get("candidate_revision"),
                ),
            )
        )
        AssistanceReviewRequest.objects.create(review=row, request_id=ticket.request_id)
        row.state = (
            ticket.state
            if ticket.state in {"paused", "awaiting_resource", "running"}
            else "pending"
        )
        control = InferenceControl.objects.filter(pk=1).first()
        if not robot_enabled() or (control is not None and control.paused):
            row.state, row.reason_code = "paused", "awaiting_resume"
        row.save(update_fields=["state", "reason_code"])

    def reconcile(self) -> None:
        for review in AssistanceReview.objects.filter(
            state__in=["pending", "running", "paused", "awaiting_resource"]
        ).order_by("created_at")[:100]:
            self._complete(review)
        if not robot_enabled() or not AssistancePolicy.objects.filter(pk=1, active=True).exists():
            return
        self._automatic()

    @transaction.atomic
    def _complete(self, review: AssistanceReview) -> None:
        lock_monitoring_publication()
        review = AssistanceReview.objects.select_for_update().get(pk=review.id)
        if not current_review(review):
            _finish(review, "superseded", "input_changed")
            return
        if review.purpose == "condition":
            _condition(review)
            return
        responses = [
            PostgresInferenceQueries().analysis(link.request_id) for link in review.requests.all()
        ]
        if not responses:
            return
        states = {str(response["state"]) for response in responses}
        if states - {"succeeded"}:
            _pending(review, states)
            return
        results = [
            cast(dict[str, object], part["result"])
            for response in responses
            for part in cast(list[dict[str, object]], response["parts"])
        ]
        if len(results) != 1:
            _finish(review, "failed", "invalid_output")
            return
        review.result = results[0]
        state = str(results[0].get("outcome", "failed"))
        if state not in {"supported", "conflict", "insufficient"}:
            _finish(review, "failed", "invalid_output")
            return
        _finish(review, state, "evidence_reviewed")
        publish_review(review)

    @staticmethod
    def _candidates(row: Listing) -> list[ListingObservation]:
        from garimpei.infra.repository.valuation.identity_mapper import current_identification

        key = current_identification(row).product_key
        if not key:
            return []
        candidates = (
            Listing.objects.exclude(id=row.id)
            .exclude(latest=None)
            .select_related("latest", "identity_progress__manual__observation")
            .order_by("id")
        )
        return [candidate.latest for candidate in candidates if candidate.latest][:10]

    def _automatic(self) -> None:
        rows = (
            Listing.objects.exclude(latest=None)
            .select_related("latest", "identity_progress__manual__observation")
            .order_by("id")
        )
        admitted = 0
        for row in rows:
            admitted += self._automatic_listing_safe(row)
            if admitted >= 10:
                break
        self._interests()

    def _automatic_listing_safe(self, row: Listing) -> int:
        try:
            return self._automatic_listing(row)
        except InferenceError as error:
            if error.code in {"queue_full", "paused", "insufficient_input"}:
                return 10
            raise

    @transaction.atomic
    def _automatic_listing(self, row: Listing) -> int:
        lock_monitoring_publication()
        assert row.latest is not None
        admitted = self._ensure("identity", row, None)
        for candidate in self._candidates(row):
            admitted += self._ensure("comparables", row, candidate)
        return admitted

    def _ensure(self, purpose: str, row: Listing, candidate: ListingObservation | None) -> int:
        assert row.latest is not None
        snapshot = observation_snapshot(row, purpose, candidate)
        if AssistanceReview.objects.filter(
            purpose=purpose, target_id=row.latest.id, input_signature=digest(snapshot)
        ).exists():
            return 0
        self._create(
            purpose,
            "listing_observation",
            row.latest.id,
            row.latest.ordinal,
            snapshot,
            row.latest,
            candidate,
        )
        return 1

    def _interests(self) -> None:
        for interest in MonitoringInterest.objects.filter(
            configuration__slot="active"
        ).select_related("configuration")[:10]:
            if self._interest_safe(interest):
                break

    def _interest_safe(self, interest: MonitoringInterest) -> bool:
        try:
            self._interest(interest)
            return False
        except InferenceError as error:
            if error.code == "queue_full":
                return True
            raise

    @transaction.atomic
    def _interest(self, row: MonitoringInterest) -> None:
        lock_monitoring_publication()
        snapshot = interest_snapshot(row)
        if (
            not snapshot["facts"]
            or AssistanceReview.objects.filter(
                purpose="investigation", target_id=row.id, input_signature=digest(snapshot)
            ).exists()
        ):
            return
        self._create("investigation", "interest", row.id, row.configuration.revision, snapshot)


def _ticket(row: AssistanceReview, reused: bool) -> ReviewTicket:
    return ReviewTicket(row.id, row.purpose, row.state, reused)


def _finish(row: AssistanceReview, state: str, reason: str) -> None:
    row.state, row.reason_code, row.updated_at, row.completed_at = state, reason, now(), now()
    row.save(update_fields=["state", "reason_code", "result", "updated_at", "completed_at"])


def _pending(row: AssistanceReview, states: set[str]) -> None:
    if states & {"failed", "superseded"}:
        _finish(row, "superseded" if "superseded" in states else "failed", "analysis_unavailable")
        return
    row.state = (
        "paused"
        if "paused" in states or not robot_enabled()
        else "awaiting_resource"
        if "awaiting_resource" in states
        else "running"
        if "running" in states
        else "pending"
    )
    row.reason_code = "awaiting_resume" if row.state == "paused" else "waiting_analysis"
    row.updated_at = now()
    row.save(update_fields=["state", "reason_code", "updated_at"])


def _condition(row: AssistanceReview) -> None:
    from garimpei.infra.persistence.assessment_models import ConditionAssessment

    assessment = (
        ConditionAssessment.objects.filter(observation_id=row.observation_id)
        .order_by("-generation")
        .first()
    )
    if assessment is None or assessment.status in {"waiting", "running"}:
        return
    from garimpei.infra.queries.listing.assessment_queries import PostgresAssessmentQueries

    applicable = PostgresAssessmentQueries().observation(
        assessment.listing_id, assessment.observation_id
    )
    if applicable.id != assessment.id or applicable.status == "waiting":
        _finish(row, "superseded", "condition_input_changed")
        return
    for request_id in assessment.inference_refs:
        AssistanceReviewRequest.objects.get_or_create(review=row, request_id=UUID(str(request_id)))
    row.consumed_by = [
        dict(kind="condition_assessment", id=str(assessment.id), policy=assessment.policy_version)
    ]
    row.save(update_fields=["consumed_by"])
    row.result = dict(
        assessment_id=str(assessment.id),
        condition=assessment.condition,
        sufficient=assessment.sufficient,
        inference_refs=assessment.inference_refs,
    )
    state = (
        "supported"
        if assessment.sufficient and assessment.condition == "good"
        else "failed"
        if assessment.status == "failed"
        else "insufficient"
    )
    _finish(row, state, assessment.reason)
