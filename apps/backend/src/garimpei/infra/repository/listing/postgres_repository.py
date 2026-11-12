import logging
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, replace
from datetime import datetime, timedelta
from uuid import UUID

from django.db import transaction

from garimpei.domain.listing.consolidation import Consolidated, consolidate
from garimpei.domain.listing.coverage import coverage
from garimpei.domain.listing.discovery import publication_is_new
from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Candidate, Match, canonical_url, price_change
from garimpei.domain.listing.ports import (
    Attempt,
    Clock,
    CollectionPolicy,
    ConfigurationReader,
    Revisit,
    SourceFailure,
    SupersededAttempt,
    Work,
)
from garimpei.domain.listing.scheduling import retry_schedule
from garimpei.domain.listing.scope import Scope
from garimpei.domain.listing.window import PublicationWindow
from garimpei.infra.persistence.listing_models import (
    CollectionCandidate,
    CollectionCycle,
    CollectionState,
    Listing,
    ListingEvent,
    ListingInterestMatch,
    ListingObservation,
)
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.repository.alert.first_inputs import invalidate_first_alert
from garimpei.infra.repository.listing.mapper import (
    CandidateRecord,
    decode_candidate,
    encode_candidate,
    encode_evidence,
)

logger = logging.getLogger(__name__)


class PostgresCollectionRepository:
    def __init__(
        self,
        configuration: ConfigurationReader,
        clock: Clock,
        enqueue: Callable[[UUID, int], int],
        lease_seconds: int,
        scope_transform: Callable[[Scope], Scope] | None = None,
    ) -> None:
        self._scope_transform = scope_transform
        self._configuration = configuration
        self._clock = clock
        self._enqueue = enqueue
        self._lease = timedelta(seconds=lease_seconds)

    def reconcile(self, policy: CollectionPolicy, *, recover_access: bool = False) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            scope = Scope.from_snapshot(self._configuration.execute())
            if scope is None:
                return
            if self._scope_transform is not None:
                scope = self._scope_transform(scope)
            state, _ = CollectionState.objects.get_or_create(
                configuration_id=scope.configuration_id,
                source=scope.source,
            )
            self._normalize_progress_cadence(state, policy)
            current = state.current
            changed = current is not None and (
                current.scope_key != scope.key or current.revision != scope.revision
            )
            if recover_access and state.access_suspended:
                state.access_suspended = False
                state.save(update_fields=["access_suspended"])
            now = self._clock()
            if state.monitoring_started_at is None:
                state.monitoring_started_at = now
                state.save(update_fields=["monitoring_started_at"])
            if not changed and not self._due(state, now):
                return
            if current is None or changed or current.finished_at is not None:
                current = self._start_cycle(state, current, scope)
            state.generation += 1
            state.current = current
            state.lease_until = now + timedelta(seconds=policy.lease)
            state.next_attempt_at = state.lease_until
            state.save()
            self._enqueue(current.id, state.generation)

    @staticmethod
    def _normalize_progress_cadence(state: CollectionState, policy: CollectionPolicy) -> None:
        cycle = state.current
        if cycle is None or cycle.finished_at is None or not cycle.published_count:
            return
        failures = [result for result in cycle.results.values() if result]
        if state.access_suspended or any(f["access"] for f in failures):
            return
        delay = max(policy.interval, max((f["retry_after"] for f in failures), default=0))
        due = cycle.finished_at + timedelta(seconds=delay)
        if state.source_not_before is not None:
            due = max(due, state.source_not_before)
        if state.next_attempt_at is not None and state.next_attempt_at > due:
            state.next_attempt_at, state.failures = due, 0
            state.save(update_fields=["next_attempt_at", "failures"])

    @staticmethod
    def _due(state: CollectionState, now: datetime) -> bool:
        return (
            not state.access_suspended
            and (state.source_not_before is None or state.source_not_before <= now)
            and (state.next_attempt_at is None or state.next_attempt_at <= now)
        )

    def _start_cycle(
        self, state: CollectionState, previous: CollectionCycle | None, scope: Scope
    ) -> CollectionCycle:
        if previous is not None and previous.finished_at is None:
            previous.phase = "superseded"
            previous.finished_at = self._clock()
            previous.save(update_fields=["phase", "finished_at"])
            CollectionCandidate.objects.filter(cycle=previous).delete()
        state.access_suspended = False
        return CollectionCycle.objects.create(
            state=state,
            scope_key=scope.key,
            revision=scope.revision,
            planned=[query.key for query in scope.searches],
        )

    @contextmanager
    def _owned(self, attempt: Attempt) -> Iterator[tuple[CollectionState, CollectionCycle, Scope]]:
        with transaction.atomic():
            # Use the publication lock before reading F03. It also serializes event commits.
            lock_monitoring_publication()
            scope = Scope.from_snapshot(self._configuration.execute())
            cycle = CollectionCycle.objects.filter(id=attempt.cycle_id).first()
            if scope is None or cycle is None:
                raise SupersededAttempt
            if self._scope_transform is not None:
                scope = self._scope_transform(scope)
            state = cycle.state
            now = self._clock()
            if (
                state.current_id != cycle.id
                or state.generation != attempt.generation
                or state.configuration_id != scope.configuration_id
                or cycle.scope_key != scope.key
                or state.lease_until is None
                or state.lease_until <= now
                or cycle.finished_at is not None
            ):
                raise SupersededAttempt
            state.lease_until = now + self._lease
            state.next_attempt_at = state.lease_until
            state.save(update_fields=["lease_until", "next_attempt_at"])
            window = (
                PublicationWindow(cycle.window_start, cycle.window_end)
                if cycle.window_start is not None and cycle.window_end is not None
                else None
            )
            yield state, cycle, replace(scope, window=window)

    def begin(self, attempt: Attempt) -> Work:
        with self._owned(attempt) as (_, cycle, scope):
            cycle.phase = "running"
            if cycle.started_at is None:
                cycle.started_at = self._clock()
            if cycle.window_start is None or cycle.window_end is None:
                window = PublicationWindow.ending_at(cycle.started_at)
                cycle.window_start, cycle.window_end = window.start, window.end
            cycle.save(update_fields=["phase", "started_at", "window_start", "window_end"])
            scope = replace(scope, window=PublicationWindow(cycle.window_start, cycle.window_end))
            return Work(scope, frozenset(cycle.results), cycle.scanned)

    def stage(self, attempt: Attempt, key: str, candidates: tuple[Candidate, ...]) -> None:
        with self._owned(attempt) as (_, cycle, _):
            grouped: dict[str, list[CandidateRecord]] = defaultdict(list)
            for candidate in candidates:
                grouped[candidate.external_id].append(encode_candidate(candidate))
            for external_id, new in grouped.items():
                row, _ = CollectionCandidate.objects.get_or_create(
                    cycle=cycle,
                    query_key=key,
                    external_id=external_id,
                )
                row.candidates.extend(item for item in new if item not in row.candidates)
                row.save(update_fields=["candidates"])

    def record(
        self,
        attempt: Attempt,
        key: str,
        failure: SourceFailure | None,
        window_proof: str | None = None,
    ) -> None:
        with self._owned(attempt) as (_, cycle, _):
            cycle.results[key] = (
                {
                    "reason": failure.reason,
                    "retry_after": failure.retry_after,
                    "access": failure.access,
                }
                if failure
                else None
            )
            if window_proof is not None:
                cycle.window_evidence[key] = window_proof
            cycle.save(update_fields=["results", "window_evidence"])

    def detail_targets(
        self, attempt: Attempt, *, include_known: bool = True
    ) -> tuple[Revisit, ...]:
        with self._owned(attempt) as (_, cycle, scope):
            return self._detail_targets(cycle, scope, include_known=include_known)

    def _detail_targets(
        self, cycle: CollectionCycle, scope: Scope, *, include_known: bool
    ) -> tuple[Revisit, ...]:
        # A listing that disappeared from search still belongs to interests it matched earlier.
        by_id: dict[str, set[Match]] = defaultdict(set)
        known_ids: set[str] = set()
        for row in CollectionCandidate.objects.filter(cycle=cycle).exclude(
            query_key__startswith="detail:"
        ):
            candidates = [decode_candidate(item) for item in row.candidates]
            result = consolidate(candidates, scope)
            if result.evidence.title is not None and not result.matches:
                continue
            for candidate in candidates:
                by_id[row.external_id].update(candidate.matches)
        for interest in {search.interest for search in scope.searches}:
            known = (
                ListingInterestMatch.objects.filter(
                    kind=interest.kind,
                    key=interest.key,
                    observation__listing__source=scope.source,
                )
                .values_list("observation__listing__external_id", flat=True)
                .distinct()
            )
            for external_id in known:
                known_ids.add(external_id)
                by_id[external_id].add(interest)
        if not include_known:
            staged_ids = set(
                CollectionCandidate.objects.filter(cycle=cycle).values_list(
                    "external_id", flat=True
                )
            )
            by_id = {key: value for key, value in by_id.items() if key in staged_ids}
        targets = tuple(
            Revisit(external_id, tuple(sorted(matches)), external_id in known_ids)
            for external_id, matches in sorted(by_id.items())
            if f"detail:{external_id}" not in cycle.results
        )
        planned = list(
            dict.fromkeys(cycle.planned + [f"detail:{item.external_id}" for item in targets])
        )
        if planned != cycle.planned:
            cycle.planned = planned
            cycle.save(update_fields=["planned"])
        return targets

    def set_origin(self, attempt: Attempt, point: Point | None) -> None:
        with self._owned(attempt) as (_, cycle, _):
            cycle.origin = asdict(point) if point else None
            cycle.save(update_fields=["origin"])

    def mark_scanned(self, attempt: Attempt, point: Point | None) -> None:
        with self._owned(attempt) as (_, cycle, _):
            cycle.origin = asdict(point) if point else None
            cycle.scanned = True
            cycle.save(update_fields=["origin", "scanned"])

    def publish_batch(self, attempt: Attempt, *, ready_only: bool = False) -> bool:
        with self._owned(attempt) as (state, cycle, scope):
            staged = CollectionCandidate.objects.filter(cycle=cycle)
            ready = [
                key.removeprefix("detail:")
                for key, result in cycle.results.items()
                if key.startswith("detail:") and result is None
            ]
            eligible = staged.filter(external_id__in=ready) if ready_only else staged
            identities = list(
                eligible.order_by("external_id")
                .values_list("external_id", flat=True)
                .distinct()[:20]
            )
            if not identities:
                return False
            grouped: dict[str, list[Candidate]] = defaultdict(list)
            for row in staged.filter(external_id__in=identities):
                grouped[row.external_id].extend(decode_candidate(item) for item in row.candidates)
            for candidates in grouped.values():
                self._publish(state, cycle, scope, consolidate(candidates, scope))
            staged.filter(external_id__in=identities).delete()
            cycle.save(update_fields=["diagnostics", "published_count"])
            return True

    def _publish(
        self, state: CollectionState, cycle: CollectionCycle, scope: Scope, result: Consolidated
    ) -> None:
        if result.conflicts:
            cycle.diagnostics[result.external_id] = list(result.conflicts)
        if not result.matches:
            return
        existing = Listing.objects.filter(
            source=scope.source, external_id=result.external_id
        ).exists()
        if (
            not existing
            and scope.window is not None
            and scope.window.contains(result.evidence.published_at) is False
        ):
            return
        now = self._clock()
        is_new = publication_is_new(result.evidence, state.monitoring_started_at, now)
        origin = "discovered" if is_new else "initial_load"
        listing, created = Listing.objects.get_or_create(
            source=scope.source,
            external_id=result.external_id,
            defaults={
                "canonical_url": canonical_url(result.external_id),
                "first_seen_at": now,
                "origin": origin,
            },
        )
        observed = ListingObservation.objects.filter(cycle=cycle, listing=listing).first()
        if observed is not None:
            ListingInterestMatch.objects.bulk_create(
                [
                    ListingInterestMatch(observation=observed, kind=m.kind, key=m.key)
                    for m in result.matches
                ],
                ignore_conflicts=True,
            )
            return
        silent = state.initial_completed_at is None and not (is_new or listing.discovery_emitted)
        self._append_observation(listing, cycle, scope, result, created, silent, is_new)
        invalidate_first_alert(listing.id, now)

    def _append_observation(
        self,
        listing: Listing,
        cycle: CollectionCycle,
        scope: Scope,
        result: Consolidated,
        created: bool,
        silent: bool,
        is_new: bool,
    ) -> None:
        now = self._clock()
        evidence = result.evidence
        previous = listing.known_price
        point = Point(**cycle.origin) if cycle.origin else None
        observation = ListingObservation.objects.create(
            listing=listing,
            cycle=cycle,
            ordinal=listing.ordinal + 1,
            observed_at=now,
            price=evidence.price,
            freight=evidence.freight,
            evidence=encode_evidence(evidence),
            coverage=asdict(coverage(point, scope.cep, evidence)),
            provenance=dict(result.provenance),
        )
        ListingInterestMatch.objects.bulk_create(
            [
                ListingInterestMatch(observation=observation, kind=match.kind, key=match.key)
                for match in result.matches
            ]
        )
        discovered = is_new and not listing.discovery_emitted
        kind = (
            "discovered"
            if discovered
            else "initial_load"
            if created
            else price_change(previous.price if previous else None, evidence.price)
        )
        if discovered:
            listing.discovery_emitted = True
            listing.origin = "discovered"
            silent = False
        elif kind == "initial_load":
            silent = True
        if kind:
            listing.publication_order += 1
            ListingEvent.objects.create(
                publication_order=listing.publication_order,
                listing=listing,
                observation=observation,
                previous=previous,
                kind=kind,
                silent=silent,
                occurred_at=now,
            )
        listing.ordinal = observation.ordinal
        listing.latest = observation
        if evidence.price is not None:
            listing.known_price = observation
        listing.save(
            update_fields=[
                "ordinal",
                "latest",
                "known_price",
                "publication_order",
                "origin",
                "discovery_emitted",
            ]
        )
        from garimpei.config.env import load_media_settings
        from garimpei.domain.media.media import Manifest
        from garimpei.infra.repository.media.captures import create_capture

        create_capture(observation, evidence.media or Manifest(), load_media_settings().policy, now)
        cycle.published_count += 1

    def finish(self, attempt: Attempt, policy: CollectionPolicy) -> None:
        with self._owned(attempt) as (state, cycle, _):
            self._finish(state, cycle, policy)

    def _finish(
        self, state: CollectionState, cycle: CollectionCycle, policy: CollectionPolicy
    ) -> None:
        now = self._clock()
        failures = [result for result in cycle.results.values() if result]
        pending = set(cycle.planned) - cycle.results.keys()
        degraded = bool(failures or pending or cycle.diagnostics)
        if degraded:
            outcome = retry_schedule(
                policy,
                state.failures,
                progress=cycle.published_count > 0,
                failures=tuple(
                    SourceFailure(f["reason"], f["retry_after"], access=f["access"])
                    for f in failures
                ),
            )
            state.failures, delay, state.access_suspended = (
                outcome.failures,
                outcome.delay,
                outcome.suspended,
            )
            cycle.phase = "partial" if cycle.published_count else "unavailable"
        else:
            if state.initial_completed_at is None:
                state.initial_completed_at = now
                state.initial_scope = cycle.scope_key
            state.last_success_at = now
            state.failures = 0
            delay = policy.interval
            cycle.phase = "complete"
        CollectionCandidate.objects.filter(cycle=cycle).delete()
        state.lease_until = None
        state.next_attempt_at = now + timedelta(seconds=delay)
        cycle.finished_at = now
        cycle.save(update_fields=["phase", "finished_at"])
        state.save()
        reasons = sorted({failure["reason"] for failure in failures})
        logger.info(
            "collection_finished",
            extra={
                "event": "collection_finished",
                "collection_cycle": str(cycle.id),
                "collection_revision": cycle.revision,
                "collection_phase": cycle.phase,
                "collection_reasons": reasons,
                "collection_observations": cycle.published_count,
            },
        )
