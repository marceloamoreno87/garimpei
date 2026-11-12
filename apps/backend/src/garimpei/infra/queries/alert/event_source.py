from dataclasses import dataclass
from typing import cast

from garimpei.config.env import load_assessment_enabled
from garimpei.domain.listing.condition import Choice
from garimpei.domain.listing.condition_resolution import resolve_condition
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.scope import Scope
from garimpei.infra.persistence.alert_models import ManualConditionHistory
from garimpei.infra.persistence.listing_models import Listing, ListingEvent, ManualCondition
from garimpei.infra.queries.listing.assessment_queries import PostgresAssessmentQueries
from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
from garimpei.infra.repository.listing.mapper import decode_evidence


@dataclass(frozen=True)
class EventCondition:
    condition: str
    revision: int
    reason: str | None = None


def event_condition(event: ListingEvent) -> EventCondition:
    assessment = (
        PostgresAssessmentQueries().observation(event.listing_id, event.observation_id)
        if load_assessment_enabled()
        else None
    )
    evidence = decode_evidence(event.observation.evidence)
    if event.publication_order is None:
        if ManualCondition.objects.filter(listing_id=event.listing_id).exists():
            return EventCondition("unavailable", 0, "condition_history_unavailable")
        state = resolve_condition(evidence, assessment)
    else:
        history = (
            ManualConditionHistory.objects.filter(
                listing_id=event.listing_id, publication_order__lt=event.publication_order
            )
            .order_by("-publication_order")
            .first()
        )
        state = resolve_condition(
            evidence,
            assessment,
            cast(Choice, history.choice) if history else None,
            history.revision if history else 0,
        )
    reason = (
        "waiting_condition_assessment"
        if assessment and not state.satisfies_alert_condition and state.effective != "defect"
        else None
    )
    return EventCondition(state.effective, state.revision, reason)


def current_eligibility(
    listing: Listing, configuration: ConfigurationReader, queries: PostgresListingQueries
) -> str:
    scope = Scope.from_snapshot(configuration.execute())
    view = queries.listing(listing.id, scope)
    if view is None:
        return "listing_missing"
    if not view.scope_current:
        return "waiting_scope"
    if not view.observation.interests:
        return "scope_excluded"
    if view.observation.evidence.source_available is not True:
        return "listing_unavailable"
    manual = ManualCondition.objects.filter(listing=listing).first()
    assessment = (
        PostgresAssessmentQueries().observation(listing.id, view.observation.id)
        if load_assessment_enabled()
        else None
    )
    state = resolve_condition(
        view.observation.evidence,
        assessment,
        cast(Choice, manual.choice) if manual else None,
    )
    if (
        assessment is not None
        and not state.satisfies_alert_condition
        and state.effective != "defect"
    ):
        return "waiting_condition_assessment"
    return "eligible" if state.satisfies_alert_condition else "condition_excluded"


def covered(event: ListingEvent) -> bool:
    return decode_evidence(event.observation.evidence).source_available is True
