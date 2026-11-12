from typing import cast
from uuid import UUID

from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.listing import InterestKind, Match
from garimpei.domain.listing.read_models import (
    Change,
    ChangePage,
    CollectionStatus,
    ListingView,
    Observation,
)
from garimpei.domain.listing.scope import Scope
from garimpei.infra.persistence.listing_models import (
    CollectionCycle,
    CollectionState,
    Listing,
    ListingEvent,
    ListingObservation,
)
from garimpei.infra.repository.listing.mapper import decode_evidence


def _observation(row: ListingObservation) -> Observation:
    return Observation(
        row.id,
        row.observed_at,
        row.cycle.revision,
        row.cycle.scope_key,
        decode_evidence(row.evidence),
        Coverage(**row.coverage),
        tuple(sorted(row.provenance.items())),
        tuple(
            Match(cast(InterestKind, item.kind), item.key)
            for item in row.matches.order_by("kind", "key")
        ),
    )


class PostgresListingQueries:
    def listing(self, identity: UUID, scope: Scope | None) -> ListingView | None:
        listing = Listing.objects.select_related("latest__cycle__state").filter(id=identity).first()
        if listing is None or listing.latest is None:
            return None
        row = listing.latest
        observation = _observation(row)
        current = scope is not None and (
            scope.key == observation.scope_key
            and scope.configuration_id == row.cycle.state.configuration_id
        )
        detail_key = f"detail:{listing.external_id}"
        stale_reason = (
            "listing_unavailable"
            if observation.evidence.source_available is False
            else self._detail_failure(scope, detail_key)
        )
        last_valid = self._last_valid(listing, detail_key) if stale_reason else None
        return ListingView(
            listing.id,
            listing.source,
            listing.external_id,
            listing.canonical_url,
            listing.first_seen_at,
            listing.origin,
            observation,
            current,
            observation.coverage
            if current
            else Coverage("unknown", "unknown", None, "scope_changed", "scope_changed"),
            observation.evidence.freight
            if current and scope and observation.evidence.freight_cep == scope.cep
            else None,
            stale_reason,
            last_valid,
        )

    @staticmethod
    def _detail_failure(scope: Scope | None, detail_key: str) -> str | None:
        if scope is None:
            return None
        cycle = (
            CollectionCycle.objects.filter(
                state__configuration_id=scope.configuration_id,
                state__source=scope.source,
                scope_key=scope.key,
                results__has_key=detail_key,
            )
            .exclude(phase="superseded")
            .order_by("-started_at", "-id")
            .first()
        )
        if cycle is None:
            return None
        issue = cycle.results[detail_key]
        return str(issue["reason"]) if issue else None

    @staticmethod
    def _last_valid(listing: Listing, detail_key: str) -> Observation | None:
        for row in listing.observations.select_related("cycle").order_by("-ordinal"):
            if (
                detail_key in row.cycle.results
                and row.cycle.results[detail_key] is None
                and row.evidence.get("source_available") is not False
            ):
                return _observation(row)
        return None

    @staticmethod
    def _state(scope: Scope | None) -> CollectionState | None:
        if scope is None:
            return None
        return (
            CollectionState.objects.select_related("current")
            .filter(
                configuration_id=scope.configuration_id,
                source=scope.source,
            )
            .first()
        )

    def status(self, scope: Scope | None) -> CollectionStatus:
        state = self._state(scope)
        if state is None or state.current is None:
            return CollectionStatus()
        cycle = state.current
        current = scope is not None and cycle.scope_key == scope.key
        return CollectionStatus(
            phase=cycle.phase if current else "scheduled",
            scope_current=current,
            initial_completed_at=state.initial_completed_at,
            last_success_at=state.last_success_at,
            last_attempt_at=cycle.finished_at or cycle.started_at,
            next_attempt_at=state.next_attempt_at,
            reason=self._reason(cycle) if current else None,
            window_start=cycle.window_start,
            window_end=cycle.window_end,
            window_proofs=tuple(sorted(cycle.window_evidence.items())),
            monitoring_started_at=state.monitoring_started_at,
            access_suspended=state.access_suspended,
        )

    @staticmethod
    def _reason(cycle: CollectionCycle) -> str | None:
        reasons = sorted({result["reason"] for result in cycle.results.values() if result})
        if reasons:
            return ", ".join(reasons)
        return "conflicting_evidence" if cycle.diagnostics else None

    def changes(self, after: int | None, limit: int) -> ChangePage:
        rows = (
            ListingEvent.objects.select_related("listing", "observation", "previous")
            .filter(
                sequence__gt=after if after is not None else 0,
            )
            .order_by("sequence")[:limit]
        )
        events = tuple(
            Change(
                row.sequence,
                row.id,
                row.kind,
                row.listing.id,
                row.observation.id,
                row.occurred_at,
                row.silent,
                Coverage(**row.observation.coverage),
                row.observation.price,
                row.previous.price if row.previous else None,
                row.previous.id if row.previous else None,
                row.previous.observed_at if row.previous else None,
                publication_order=row.publication_order,
            )
            for row in rows
        )
        return ChangePage(events, events[-1].sequence if events else after)
