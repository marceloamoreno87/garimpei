from dataclasses import dataclass
from typing import cast

from garimpei.domain.listing.condition import Choice, ConditionState, automatic_condition
from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.scope import Scope
from garimpei.infra.persistence.alert_models import ManualConditionHistory
from garimpei.infra.persistence.listing_models import Listing, ListingEvent, ManualCondition
from garimpei.infra.queries.listing.postgres_queries import PostgresListingQueries
from garimpei.infra.repository.listing.mapper import decode_evidence


@dataclass(frozen=True)
class EventCondition:
    condition: str
    revision: int
    reason: str | None = None


def event_condition(event: ListingEvent) -> EventCondition:
    automatic = automatic_condition(decode_evidence(event.observation.evidence))
    if event.publication_order is None:
        if ManualCondition.objects.filter(listing_id=event.listing_id).exists():
            return EventCondition("unavailable", 0, "condition_history_unavailable")
        return EventCondition(automatic.condition, 0)
    history = (
        ManualConditionHistory.objects.filter(
            listing_id=event.listing_id, publication_order__lt=event.publication_order
        )
        .order_by("-publication_order")
        .first()
    )
    if history is None:
        return EventCondition(automatic.condition, 0)
    return EventCondition(cast(Choice, history.choice), history.revision)


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
    state = ConditionState(
        automatic_condition(view.observation.evidence),
        cast(Choice, manual.choice) if manual else None,
    )
    return "eligible" if state.effective == "good" else "condition_excluded"


def covered(event: ListingEvent) -> bool:
    return decode_evidence(event.observation.evidence).source_available is True
