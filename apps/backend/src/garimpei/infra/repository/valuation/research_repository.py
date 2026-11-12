from collections.abc import Callable
from dataclasses import asdict
from datetime import timedelta

from django.db import transaction
from django.db.models import Max, Q

from garimpei.domain.listing.listing import Candidate
from garimpei.domain.listing.ports import (
    Clock,
    ConfigurationReader,
    Page,
    SourceFailure,
    SupersededAttempt,
)
from garimpei.domain.listing.scope import Scope
from garimpei.domain.valuation.policy import VALUATION_POLICY, estimate
from garimpei.domain.valuation.research import ResearchUnit
from garimpei.domain.valuation.research_limits import ResearchLimits
from garimpei.infra.persistence.listing_models import (
    CollectionCycle,
    CollectionState,
    Listing,
    ListingInterestMatch,
)
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.persistence.research_models import (
    ComparableInvestigation,
    InvestigationTarget,
    ResearchQuery,
)
from garimpei.infra.repository.listing.mapper import encode_candidate
from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
from garimpei.infra.repository.valuation.identity_mapper import identify_row
from garimpei.infra.repository.valuation.postgres_repository import _listing
from garimpei.infra.repository.valuation.research_mapper import (
    digest,
    policy_snapshot,
    research_term,
    unit,
)
from garimpei.infra.repository.valuation.research_targets import (
    record_decisions,
    refresh_targets,
    sufficient,
)

ACTIVE = ("pending", "waiting_evidence", "waiting_retry", "running")


class PostgresComparableResearchRepository:
    def __init__(
        self,
        configuration: ConfigurationReader,
        clock: Clock,
        limits: ResearchLimits | None,
        publication: PostgresCollectionRepository,
        scope_transform: Callable[[Scope], Scope] | None = None,
    ) -> None:
        self._scope_transform = scope_transform
        self._configuration, self._clock, self._limits, self._publication = (
            configuration,
            clock,
            limits,
            publication,
        )

    def _scope(self) -> Scope | None:
        scope = Scope.from_snapshot(self._configuration.execute())
        return (
            self._scope_transform(scope) if scope is not None and self._scope_transform else scope
        )

    def reconcile(self) -> None:
        if self._limits is None:
            return
        scope = self._scope()
        if scope is None:
            return
        listings = tuple(
            Listing.objects.select_related("latest", "identity_progress__manual__observation")
            .filter(latest__isnull=False)
            .exclude(origin="reference")
        )
        candidates = tuple(
            _listing(row, identify_row(row, getattr(row, "identity_progress", None)))
            for row in listings
        )
        for listing, candidate in zip(listings, candidates, strict=True):
            if (
                candidate.product is None
                or estimate(candidate, candidates, self._clock()).price is not None
            ):
                continue
            self._request(scope, listing, candidate.product)

    @transaction.atomic
    def _request(self, scope: Scope, listing: Listing, product: str) -> None:
        lock_monitoring_publication()
        assert self._limits is not None
        listing.refresh_from_db()
        current = identify_row(listing, getattr(listing, "identity_progress", None))
        if (
            current.state != "identified"
            or current.product_key != product
            or listing.latest is None
        ):
            return
        active = {(s.interest.kind, s.interest.key) for s in scope.searches}
        matches = sorted(
            {
                (m.kind, m.key)
                for m in ListingInterestMatch.objects.filter(observation=listing.latest)
            }
            & active
        )
        if not matches:
            return
        context = dict(
            source=scope.source,
            cep=scope.cep,
            modality="marketplace",
            radius_km=500,
            used_observation_window_days=14,
            publication_age_limit=None,
            configuration_id=str(scope.configuration_id),
            revision=scope.revision,
            scope_key=scope.key,
        )
        signature = digest([product, context, VALUATION_POLICY, self._limits.policy_version])
        existing = ComparableInvestigation.objects.filter(signature=signature).first()
        interest = ":".join(matches[0])
        if (
            existing is None
            and ComparableInvestigation.objects.filter(
                origin_interest=interest, state__in=ACTIVE
            ).count()
            >= self._limits.max_pending_per_interest
        ):
            return
        pending_interests = set(
            ComparableInvestigation.objects.filter(state__in=ACTIVE).values_list(
                "origin_interest", flat=True
            )
        )
        wait_limited = (
            interest not in pending_interests
            and len(pending_interests) >= self._limits.max_wait_slices_per_interest
        )
        row, _ = ComparableInvestigation.objects.get_or_create(
            signature=signature,
            defaults=dict(
                product_key=product,
                configuration_id=scope.configuration_id,
                configuration_revision=scope.revision,
                origin_interest=interest,
                scope_key=scope.key,
                context=context,
                limits=policy_snapshot(self._limits),
                term=research_term(product),
                policy=VALUATION_POLICY,
                requested_at=self._clock(),
                next_attempt_at=self._clock(),
            ),
        )
        if wait_limited and existing is None:
            row.state, row.reason = "limited", "interest_wait_budget_exceeded"
            row.save(update_fields=["state", "reason"])
        InvestigationTarget.objects.filter(listing=listing, active=True).exclude(
            investigation=row, observation=listing.latest, manual_revision=current.manual_revision
        ).update(active=False)
        InvestigationTarget.objects.get_or_create(
            investigation=row,
            listing=listing,
            observation=listing.latest,
            manual_revision=current.manual_revision,
            defaults=dict(configuration_revision=scope.revision),
        )

    @transaction.atomic
    def claim(self) -> ResearchUnit | None:
        if self._limits is None:
            return None
        lock_monitoring_publication()
        scope = self._scope()
        if scope is None:
            return None
        now = self._clock()
        rows = (
            ComparableInvestigation.objects.select_for_update()
            .filter(state__in=ACTIVE)
            .filter(Q(next_attempt_at=None) | Q(next_attempt_at__lte=now))
            .filter(Q(lease_until=None) | Q(lease_until__lte=now))
            .order_by("last_turn", "requested_at", "id")
        )
        interest_turns = {
            entry["origin_interest"]: entry["last"]
            for entry in ComparableInvestigation.objects.values("origin_interest").annotate(
                last=Max("last_turn")
            )
        }
        ordered = sorted(
            rows,
            key=lambda r: (
                interest_turns.get(r.origin_interest) or 0,
                r.last_turn,
                r.requested_at,
                str(r.id),
            ),
        )
        row = self._next_valid(ordered, scope)
        if row is None:
            return None
        if row.cycle is None:
            state, _ = CollectionState.objects.get_or_create(
                configuration_id=scope.configuration_id, source=scope.source
            )
            row.cycle = CollectionCycle.objects.create(
                state=state,
                scope_key=scope.key,
                revision=scope.revision,
                planned=[],
                phase="running",
                started_at=now,
            )
        maximum = (
            ComparableInvestigation.objects.order_by("-last_turn")
            .values_list("last_turn", flat=True)
            .first()
            or 0
        )
        row.last_turn, row.generation, row.attempts = (
            maximum + 1,
            row.generation + 1,
            row.attempts + 1,
        )
        row.lease_until, row.state = now + timedelta(seconds=self._limits.lease_seconds), "running"
        row.next_attempt_at = row.lease_until
        row.save()
        return unit(row, scope)

    def _next_valid(
        self, rows: list[ComparableInvestigation], scope: Scope
    ) -> ComparableInvestigation | None:
        assert self._limits is not None
        for row in rows:
            if (
                row.scope_key != scope.key
                or row.configuration_revision != scope.revision
                or not refresh_targets(row)
            ):
                self._terminal(row, "superseded", "input_revision_changed")
                continue
            if row.attempts >= self._limits.max_attempts_per_input:
                self._terminal(row, "limited", "attempt_budget_reached")
                continue
            return row
        return None

    def _owned(self, work: ResearchUnit) -> ComparableInvestigation:
        lock_monitoring_publication()
        row = ComparableInvestigation.objects.select_for_update().get(id=work.id)
        scope = self._scope()
        if (
            scope is None
            or row.generation != work.generation
            or row.lease_until is None
            or row.lease_until <= self._clock()
            or scope.key != row.scope_key
            or scope.revision != row.configuration_revision
            or not refresh_targets(row)
        ):
            raise SupersededAttempt()
        return row

    @transaction.atomic
    def page(self, work: ResearchUnit, page: Page) -> ResearchUnit | None:
        row = self._owned(work)
        context = page.source_context
        now = self._clock()
        query = ResearchQuery.objects.create(
            investigation=row,
            ordinal=row.pages + 1,
            term=row.term,
            requested=dict(
                **row.context,
                term=row.term,
                sort="creation_time_descend",
                window_start=work.scope.window.start.isoformat() if work.scope.window else None,
                window_end=work.scope.window.end.isoformat() if work.scope.window else None,
            ),
            observed=asdict(context) if context else {},
            state="verified"
            if context
            and context.verified
            and context.radius_km == 500
            and context.query == row.term
            else "partial",
            reason=page.diagnostic or "",
            requested_at=now,
            confirmed_at=now,
        )
        row.pages += page.traversed_pages
        if page.diagnostic == "native_cursor_unavailable":
            row.context["partial_reason"] = page.diagnostic
        if page.invalid_cards:
            row.context["partial_reason"] = row.context.get(
                "partial_reason", "invalid_source_cards"
            )
        if query.state != "verified" or (
            page.diagnostic and page.diagnostic != "native_cursor_unavailable"
        ):
            return self._terminal(row, "limited", page.diagnostic or "search_geography_unverified")
        signature = digest(sorted(c.external_id for c in page.candidates))
        if signature in row.signatures or (
            page.continuation is not None and page.continuation == row.cursor
        ):
            return self._terminal(row, "limited", "repeated_page_or_cursor")
        row.signatures.append(signature)
        confirmed = set(
            row.queries.values_list("decisions__observation__listing__external_id", flat=True)
        )
        unique = {
            candidate.external_id: candidate
            for candidate in page.candidates
            if candidate.external_id not in confirmed
        }
        row.buffer = [
            dict(external_id=c.external_id, query_id=str(query.id), card=encode_candidate(c))
            for c in unique.values()
        ]
        row.cursor = page.continuation
        row.last_progress_at = now
        row.save()
        if not row.buffer and (row.cursor is None or row.pages >= work.limits.max_pages_per_query):
            if row.context.get("partial_reason"):
                return self._terminal(row, "limited", str(row.context["partial_reason"]))
            return self._terminal(
                row,
                "exhausted" if row.cursor is None else "limited",
                "no_results" if row.cursor is None else "page_budget_reached",
            )
        return unit(row, work.scope)

    @transaction.atomic
    def detail(self, work: ResearchUnit, candidate: Candidate) -> ResearchUnit | None:
        row = self._owned(work)
        if not row.buffer or candidate.external_id != row.buffer[0]["external_id"]:
            raise SourceFailure("unverified_identity")
        assert row.cycle is not None
        query = ResearchQuery.objects.get(id=row.buffer[0]["query_id"])
        observation = self._publication.publish_reference(work.scope, row.cycle, candidate)
        record_decisions(row, query, observation, self._clock())
        row.buffer = row.buffer[1:]
        row.details += 1
        row.last_progress_at = self._clock()
        row.failures = 0
        row.save()
        if sufficient(row, self._clock()):
            return self._terminal(row, "sufficient", "five_retained_comparables")
        if not row.buffer and (row.cursor is None or row.pages >= work.limits.max_pages_per_query):
            if row.context.get("partial_reason"):
                return self._terminal(row, "limited", str(row.context["partial_reason"]))
            return self._terminal(
                row,
                "exhausted" if row.cursor is None else "limited",
                "source_exhausted" if row.cursor is None else "page_budget_reached",
            )
        return unit(row, work.scope)

    @transaction.atomic
    def failed(self, work: ResearchUnit, failure: SourceFailure) -> None:
        row = self._owned(work)
        row.failures += 1
        if work.pending and not failure.access and not failure.retry_after:
            self._detail_failure(row, failure)
        row.state = (
            "suspended_access"
            if failure.access
            else "limited"
            if row.attempts >= work.limits.max_attempts_per_input
            else "waiting_retry"
        )
        row.reason = failure.reason
        delay = work.limits.retry_delays_seconds[
            min(row.failures - 1, len(work.limits.retry_delays_seconds) - 1)
        ]
        row.next_attempt_at = self._clock() + timedelta(seconds=max(delay, failure.retry_after))
        row.lease_until = None
        row.save()

    @transaction.atomic
    def yield_slice(self, work: ResearchUnit) -> None:
        row = self._owned(work)
        row.state, row.reason, row.lease_until = "waiting_evidence", "slice_budget_yielded", None
        row.next_attempt_at = self._clock()
        row.save(update_fields=["state", "reason", "lease_until", "next_attempt_at"])

    @staticmethod
    def _terminal(row: ComparableInvestigation, state: str, reason: str) -> None:
        row.state, row.reason, row.lease_until = state, reason, None
        row.save()
        if row.cycle is not None:
            row.cycle.phase, row.cycle.finished_at = (
                "complete" if state == "sufficient" else "partial",
                row.last_progress_at or row.requested_at,
            )
            row.cycle.save(update_fields=["phase", "finished_at"])

    @staticmethod
    def _detail_failure(row: ComparableInvestigation, failure: SourceFailure) -> None:
        pending = row.buffer[0]
        pending["failures"] = int(pending.get("failures", 0)) + 1
        if pending["failures"] < 3:
            return
        query = ResearchQuery.objects.get(id=pending["query_id"])
        rejected = query.observed.setdefault("detail_failures", [])
        rejected.append(
            dict(
                external_id=pending["external_id"],
                card=pending["card"],
                reason=failure.reason,
                attempts=pending["failures"],
                detail_confirmed=False,
            )
        )
        query.save(update_fields=["observed"])
        row.buffer = row.buffer[1:]
