"""Compare complete input context before binding a local result to a consumer."""

from typing import cast
from uuid import UUID

from django.utils.timezone import now

from garimpei.infra.gateway.assistance.snapshots import (
    digest,
    interest_snapshot,
    observation_snapshot,
    operations_snapshot,
)
from garimpei.infra.persistence.assistance_models import (
    AssistanceOperationsSnapshot,
    AssistanceReview,
)
from garimpei.infra.persistence.identity_models import IdentityProgress
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.monitoring_models import MonitoringInterest
from garimpei.infra.persistence.valuation_models import ValuationProgress


def current_review(row: AssistanceReview) -> bool:
    if row.target_kind == "operations_snapshot":
        current = AssistanceOperationsSnapshot.objects.order_by("-revision").first()
        return bool(
            current
            and current.id == row.target_id
            and digest(operations_snapshot(current)) == row.input_signature
        )
    if row.target_kind == "interest":
        interest = (
            MonitoringInterest.objects.select_related("configuration")
            .filter(id=row.target_id, configuration__slot="active")
            .first()
        )
        return bool(interest and digest(interest_snapshot(interest)) == row.input_signature)
    if row.observation is None:
        return False
    listing = (
        Listing.objects.select_related("latest", "identity_progress__manual__observation")
        .filter(id=row.observation.listing_id)
        .first()
    )
    if listing is None or listing.latest_id != row.observation_id:
        return False
    if (
        row.candidate_observation_id
        and row.candidate_observation
        and row.candidate_observation.listing.latest_id != row.candidate_observation_id
    ):
        return False
    return (
        digest(observation_snapshot(listing, row.purpose, row.candidate_observation))
        == row.input_signature
    )


def publish_review(row: AssistanceReview) -> None:
    if row.purpose == "identity" and row.observation is not None:
        progress = (
            IdentityProgress.objects.select_related("current")
            .filter(listing_id=row.observation.listing_id)
            .first()
        )
        if progress and progress.current and progress.current.observation_id == row.observation_id:
            snapshot = dict(progress.current.result)
            snapshot["assistance"] = dict(
                review_id=str(row.id), state=row.state, manual_preserved=True
            )
            progress.current.result = snapshot
            progress.current.save(update_fields=["result"])
            consume(row, "normalization", str(progress.current.id))
    if row.purpose in {"identity", "comparables"} and row.observation:
        ValuationProgress.objects.filter(listing_id=row.observation.listing_id).update(
            due_at=now(), signature=""
        )


def consume(row: AssistanceReview, kind: str, identity: str) -> None:
    consumers = cast(list[dict[str, str]], row.consumed_by)
    value = dict(kind=kind, id=identity, policy="assisted-evidence-v1")
    if value not in consumers:
        row.consumed_by = [*consumers, value]
        row.save(update_fields=["consumed_by"])


def applicable_review(
    observation_id: UUID, purpose: str, candidate_id: UUID | None = None
) -> AssistanceReview | None:
    rows = (
        AssistanceReview.objects.filter(
            observation_id=observation_id, purpose=purpose, candidate_observation_id=candidate_id
        )
        .select_related("observation", "candidate_observation__listing")
        .order_by("-generation")
    )
    return next((row for row in rows if current_review(row)), None)
