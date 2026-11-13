import hashlib
from dataclasses import replace
from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Max

from garimpei.domain.listing.listing import Candidate, canonical_url
from garimpei.domain.listing.ports import Clock, ConfigurationReader, Page, SourceFailure
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.navigation.catalog import Catalog, Relation
from garimpei.domain.navigation.policy import (
    NavigationPolicy,
    decide_suggestion,
    eligible_suggestion,
    suggestion_capacity,
)
from garimpei.domain.navigation.work import SuggestionUnit
from garimpei.infra.persistence.listing_models import CollectionState
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.persistence.navigation_models import NicheSuggestion, SuggestionEvidence
from garimpei.infra.repository.robot.postgres_repository import robot_enabled


class PostgresSuggestionRepository:
    def __init__(
        self,
        configuration: ConfigurationReader,
        catalog: Catalog,
        policy: NavigationPolicy,
        clock: Clock,
        timeout: int,
        cadence: float,
    ) -> None:
        self._configuration, self._catalog, self._policy, self._clock = (
            configuration,
            catalog,
            policy,
            clock,
        )
        self._timeout, self._cadence = timeout, cadence

    def _scope(self) -> Scope | None:
        return Scope.from_snapshot(self._configuration.execute())

    @transaction.atomic
    def claim(self) -> SuggestionUnit | None:
        lock_monitoring_publication()
        if not robot_enabled():
            return None
        scope, now = self._scope(), self._clock()
        if scope is None:
            return None
        state = CollectionState.objects.filter(
            configuration_id=scope.configuration_id, source=scope.source
        ).first()
        if state is None or state.current is None:
            return None
        active_ready = state.current.finished_at is None
        last = NicheSuggestion.objects.filter(configuration_id=scope.configuration_id).aggregate(
            last=Max("last_slice_at")
        )["last"]
        if not decide_suggestion(
            self._policy,
            now,
            active_ready=active_ready,
            active_due=state.next_attempt_at,
            last_slice=last,
            timeout=self._timeout,
            cadence=self._cadence,
            source_until=state.source_not_before,
            suspended=state.access_suspended,
        ).allowed:
            return None
        pairs = [
            (query, relation)
            for query in scope.searches
            for relation in self._catalog.related(query.term)
        ]
        for query, relation in pairs:
            unit = self._reserve(scope, query, relation, now)
            if unit is not None:
                return unit
        return None

    def _reserve(
        self, scope: Scope, query: Search, relation: Relation, now: datetime
    ) -> SuggestionUnit | None:
        row = NicheSuggestion.objects.filter(
            configuration_id=scope.configuration_id,
            origin_interest=query.key,
            term=relation.target,
            relation_key=relation.key,
        ).first()
        count = NicheSuggestion.objects.filter(configuration_id=scope.configuration_id).count()
        if suggestion_capacity(
            self._policy, new_suggestion=row is None, suggestion_count=count, evidence_count=0
        ):
            return None
        row, _ = NicheSuggestion.objects.get_or_create(
            configuration_id=scope.configuration_id,
            origin_interest=query.key,
            term=relation.target,
            relation_key=relation.key,
            defaults=dict(
                revision=scope.revision,
                original_term=query.term,
                catalog_version=self._catalog.version,
                relation_reason=relation.reason,
            ),
        )
        limit = suggestion_capacity(
            self._policy,
            new_suggestion=False,
            suggestion_count=count,
            evidence_count=row.evidence.count(),
        )
        if limit or row.state == "limited":
            row.state, row.reason = "limited", limit or row.reason
            row.save(update_fields=["state", "reason"])
            return None
        row.revision, row.last_slice_at = scope.revision, now
        row.reason = "idle_budget_reserved"
        row.pages = row.details = 0
        row.save()
        return SuggestionUnit(
            row.id,
            scope,
            replace(
                query, term=relation.target, equivalent_terms=self._catalog.terms(relation.target)
            ),
            relation.key,
            now,
            row.pending_id,
        )

    def _owned(self, unit: SuggestionUnit) -> NicheSuggestion | None:
        lock_monitoring_publication()
        scope = self._scope()
        row = NicheSuggestion.objects.select_for_update().get(id=unit.id)
        state = CollectionState.objects.filter(
            configuration_id=unit.scope.configuration_id, source=unit.scope.source
        ).first()
        if (
            scope is None
            or scope.revision != unit.scope.revision
            or scope.key != unit.scope.key
            or row.last_slice_at != unit.generation_at
            or row.relation_key != unit.relation_key
            or state is None
            or state.access_suspended
        ):
            return None
        if state.current is None or state.current.finished_at is None:
            return None
        if not eligible_suggestion(
            self._policy,
            self._clock(),
            active_ready=False,
            active_due=state.next_attempt_at,
            last_slice=None,
            timeout=self._timeout,
            cadence=self._cadence,
        ):
            return None
        return row

    @transaction.atomic
    def page(self, unit: SuggestionUnit, page: Page) -> str | None:
        row = self._owned(unit)
        if row is None:
            return None
        row.pages += page.traversed_pages
        row.reason = page.diagnostic or "evidence_pending"
        candidate = (
            next(
                (
                    item
                    for item in page.candidates
                    if item.external_id.isdecimal()
                    and item.evidence.title
                    and self._catalog.matches(row.term, item.evidence.title)
                ),
                None,
            )
            if not page.diagnostic
            else None
        )
        row.pending_id = candidate.external_id if candidate else ""
        row.save()
        return row.pending_id or None

    @transaction.atomic
    def confirm(self, unit: SuggestionUnit, candidate: Candidate) -> None:
        row = self._owned(unit)
        if row is None:
            return
        row.details += 1
        title = candidate.evidence.title
        if (
            row.pending_id != candidate.external_id
            or not candidate.external_id.isdecimal()
            or title is None
            or not self._catalog.matches(row.term, title)
        ):
            row.reason = "identity_unverified"
            row.save()
            return
        if row.evidence.count() >= self._policy.evidence_limit:
            row.state, row.reason = "limited", "evidence_limit"
            row.save()
            return
        SuggestionEvidence.objects.get_or_create(
            suggestion=row,
            source=unit.scope.source,
            external_id=candidate.external_id,
            catalog_version=self._catalog.version,
            defaults=dict(
                canonical_url=canonical_url(candidate.external_id),
                excerpt=title[:500],
                observed_at=self._clock(),
                context_hash=hashlib.sha256(
                    f"{unit.scope.key}:{unit.scope.revision}:{unit.query.term}".encode()
                ).hexdigest(),
            ),
        )
        row.state, row.reason, row.observed_at, row.pending_id = (
            "supported",
            "related_listing_verified",
            self._clock(),
            "",
        )
        row.save()

    @transaction.atomic
    def failed(self, unit: SuggestionUnit, failure: SourceFailure) -> None:
        lock_monitoring_publication()
        NicheSuggestion.objects.filter(id=unit.id, last_slice_at=unit.generation_at).update(
            reason=failure.reason
        )
        if failure.access:
            CollectionState.objects.filter(
                configuration_id=unit.scope.configuration_id, source=unit.scope.source
            ).update(access_suspended=True)
        elif failure.retry_after:
            state = CollectionState.objects.get(
                configuration_id=unit.scope.configuration_id, source=unit.scope.source
            )
            deadline = self._clock() + timedelta(seconds=failure.retry_after)
            state.source_not_before = max(state.source_not_before or deadline, deadline)
            state.next_attempt_at = max(state.next_attempt_at or deadline, deadline)
            state.save(update_fields=["source_not_before", "next_attempt_at"])
