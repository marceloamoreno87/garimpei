"""Short transactions join public F04 publication and F13 receipts/checkpoints."""

import hashlib
from collections.abc import Callable
from dataclasses import replace
from datetime import timedelta
from uuid import UUID

from django.db import transaction
from django.db.models import Max, Sum

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Candidate
from garimpei.domain.listing.ports import (
    Attempt,
    Clock,
    CollectionPolicy,
    CollectionStore,
    ConfigurationReader,
    Page,
    SourceFailure,
    SupersededAttempt,
)
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.navigation.catalog import Catalog
from garimpei.domain.navigation.policy import NavigationPolicy, select_turn
from garimpei.domain.navigation.ports import MissingNavigation, StaleNavigation
from garimpei.domain.navigation.work import NavigationUnit
from garimpei.infra.persistence.listing_models import (
    CollectionCycle,
    CollectionState,
    ListingObservation,
)
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.persistence.navigation_models import (
    NavigationCheckpoint,
    NavigationUnitReceipt,
    NavigationWork,
)
from garimpei.infra.repository.listing.mapper import decode_candidate, encode_candidate
from garimpei.infra.repository.navigation.mapper import to_unit


class PostgresNavigationRepository:
    def __init__(
        self,
        collection: CollectionStore,
        configuration: ConfigurationReader,
        catalog: Catalog,
        policy: NavigationPolicy,
        collection_policy: CollectionPolicy,
        clock: Clock,
        enqueue: Callable[[Attempt, int], None],
    ) -> None:
        self._collection, self._configuration, self._catalog = collection, configuration, catalog
        self._policy, self._collection_policy, self._clock, self._enqueue = (
            policy,
            collection_policy,
            clock,
            enqueue,
        )

    def _guard(
        self, attempt: Attempt, revision: int | None = None, *, allow_blocked: bool = False
    ) -> CollectionCycle:
        lock_monitoring_publication()
        snapshot = self._configuration.execute()
        cycle = CollectionCycle.objects.select_related("state").filter(id=attempt.cycle_id).first()
        if (
            cycle is None
            or cycle.state.current_id != cycle.id
            or cycle.state.generation != attempt.generation
            or cycle.finished_at
            or snapshot.revision != cycle.revision
            or (revision is not None and revision != snapshot.revision)
        ):
            raise SupersededAttempt
        if (
            not allow_blocked
            and cycle.state.source_not_before
            and cycle.state.source_not_before > self._clock()
        ):
            raise SupersededAttempt
        if not allow_blocked and cycle.state.access_suspended:
            raise SupersededAttempt
        return cycle

    @transaction.atomic
    def prepare(self, attempt: Attempt, scope: Scope) -> None:
        self._guard(attempt, scope.revision)
        fresh = not NavigationWork.objects.filter(
            cycle_id=attempt.cycle_id, purpose="active"
        ).exists()
        limits = self._cycle_limits(attempt.cycle_id)
        for query in scope.searches:
            for front in ("discovery", "investigation"):
                row, _ = NavigationWork.objects.get_or_create(
                    cycle_id=attempt.cycle_id,
                    origin_interest=query.key,
                    front=front,
                    purpose="active",
                    original_term=query.term,
                    defaults=dict(
                        configuration_id=scope.configuration_id,
                        source=scope.source,
                        scope_key=scope.key,
                        revision=scope.revision,
                    ),
                )
                NavigationCheckpoint.objects.get_or_create(
                    work=row,
                    defaults=dict(
                        catalog_version=self._catalog.version,
                        context_hash=hashlib.sha256(
                            f"{scope.key}:{scope.revision}:{query.key}:{query.term}:{scope.window}".encode()
                        ).hexdigest(),
                        terms=list(self._catalog.terms(query.term)[: limits["cycle_terms"]]),
                        limits=limits,
                        context=self._window_context(scope),
                    ),
                )

        self._bind_research_context(attempt, scope)
        if fresh:
            self._carry_pending(attempt, scope)

    def _bind_research_context(self, attempt: Attempt, scope: Scope) -> None:
        for checkpoint in NavigationCheckpoint.objects.filter(
            work__cycle_id=attempt.cycle_id, work__purpose="research"
        ):
            if checkpoint.context.get("window_end") is not None:
                continue
            window = self._window_context(scope)
            checkpoint.context.update(
                window_start=window["window_start"], window_end=window["window_end"]
            )
            checkpoint.context_hash = hashlib.sha256(
                f"{checkpoint.context['request_hash']}:{window['window_start']}:{window['window_end']}".encode()
            ).hexdigest()
            checkpoint.save(update_fields=["context", "context_hash"])

    def _cycle_limits(self, cycle_id: UUID) -> dict[str, int]:
        existing = (
            NavigationCheckpoint.objects.filter(work__cycle_id=cycle_id).exclude(limits={}).first()
        )
        if existing is not None:
            return {
                "cycle_pages": int(existing.limits["cycle_pages"]),
                "cycle_terms": int(existing.limits["cycle_terms"]),
            }
        return {"cycle_pages": self._policy.cycle_pages, "cycle_terms": self._policy.cycle_terms}

    @staticmethod
    def _window_context(scope: Scope) -> dict[str, str | None]:
        return {
            "window_start": scope.window.start.isoformat() if scope.window else None,
            "window_end": scope.window.end.isoformat() if scope.window else None,
            "purpose": "active",
        }

    def _carry_pending(self, attempt: Attempt, scope: Scope) -> None:
        previous = (
            NavigationWork.objects.filter(
                configuration_id=scope.configuration_id,
                scope_key=scope.key,
                revision=scope.revision,
                cycle__finished_at__isnull=False,
            )
            .exclude(cycle_id=attempt.cycle_id)
            .order_by("-cycle__finished_at")
            .first()
        )
        if previous is None:
            return
        for query in scope.searches:
            self._carry_interest(attempt, scope, previous.cycle_id, query)

    def _carry_interest(
        self, attempt: Attempt, scope: Scope, previous_id: UUID, query: Search
    ) -> None:
        checkpoints = NavigationCheckpoint.objects.filter(
            work__cycle_id=previous_id, work__origin_interest=query.key
        )
        records = {
            str(item): item for checkpoint in checkpoints for item in checkpoint.buffered_candidates
        }
        row = NavigationWork.objects.get(
            cycle_id=attempt.cycle_id,
            origin_interest=query.key,
            front="investigation",
            purpose="active",
        )
        checkpoint = NavigationCheckpoint.objects.get(work=row)
        candidates = tuple(decode_candidate(item) for item in records.values())
        self._collection.stage(attempt, query.key, candidates[: self._policy.pending_details])
        checkpoint.buffered_candidates = [
            encode_candidate(candidate) for candidate in candidates[self._policy.pending_details :]
        ]
        checkpoint.save()
        if records or checkpoints.exclude(work__phase="complete").exists():
            NavigationWork.objects.filter(
                cycle_id=attempt.cycle_id, origin_interest=query.key, front="discovery"
            ).update(reason="cursor_rebuilt")

    @transaction.atomic
    def claim(
        self, attempt: Attempt, scope: Scope, *, pages: int, details: bool
    ) -> NavigationUnit | None:
        self._guard(attempt, scope.revision)
        units = self._eligible_units(attempt, scope, pages, details)
        chosen = select_turn(tuple(unit.turn for unit in units), self._clock())
        if chosen is None:
            return None
        unit = next(unit for unit in units if unit.turn.id == chosen.id)
        row = NavigationWork.objects.get(id=unit.turn.id)
        row.generation += 1
        row.phase = "running"
        row.last_turn = (
            NavigationWork.objects.filter(cycle_id=attempt.cycle_id).aggregate(
                order=Max("last_turn")
            )["order"]
            or 0
        ) + 1
        row.save(update_fields=["generation", "phase", "last_turn"])
        NavigationWork.objects.filter(
            cycle_id=attempt.cycle_id, origin_interest=row.origin_interest, front=row.front
        ).update(last_turn=row.last_turn)
        NavigationCheckpoint.objects.filter(work=row).update(
            generation=row.generation, pending_unit=unit.unit_key
        )
        return replace(unit, generation=row.generation, turn=unit.turn.attempted(row.last_turn))

    def _eligible_units(
        self, attempt: Attempt, scope: Scope, pages: int, details: bool
    ) -> list[NavigationUnit]:
        self._drain_buffers(attempt, scope)
        targets = self._collection.detail_targets(attempt)
        queries = {query.key: query for query in scope.searches}
        units = []
        for row in NavigationWork.objects.filter(cycle_id=attempt.cycle_id).exclude(
            phase__in=["complete", "partial", "suspended", "superseded"]
        ):
            query = queries.get(row.origin_interest)
            if query is None:
                continue
            target = next((item for item in targets if query.interest in item.matches), None)
            if (row.front == "discovery" and not pages) or (
                row.front == "investigation" and (not details or target is None)
            ):
                continue
            checkpoint = NavigationCheckpoint.objects.get(work=row)
            cost = 2 if checkpoint.cursor and checkpoint.cursor.startswith("source:") else 1
            consumed = (
                NavigationCheckpoint.objects.filter(
                    work__cycle_id=attempt.cycle_id,
                    work__origin_interest=row.origin_interest,
                    work__front="discovery",
                ).aggregate(total=Sum("pages"))["total"]
                or 0
            )
            if row.front == "discovery" and consumed + cost > int(
                checkpoint.limits.get("cycle_pages", self._policy.cycle_pages)
            ):
                row.phase, row.reason = "partial", "window_limit"
                row.save(update_fields=["phase", "reason"])
                self._collection.record(attempt, row.origin_interest, SourceFailure("window_limit"))
                continue
            if (
                row.front == "discovery"
                and checkpoint.cursor
                and checkpoint.cursor.startswith("source:")
                and pages < 2
            ):
                continue
            if (
                row.front == "discovery"
                and sum(query.interest in item.matches for item in targets)
                >= self._policy.pending_details
            ):
                row.reason = "pending_details_limit"
                row.save(update_fields=["reason"])
                continue
            units.append(
                to_unit(row, checkpoint, query, target if row.front == "investigation" else None)
            )
        return units

    def _owned(
        self, attempt: Attempt, unit: NavigationUnit
    ) -> tuple[NavigationWork, NavigationCheckpoint]:
        self._guard(attempt, unit.revision)
        row = NavigationWork.objects.select_for_update().get(id=unit.turn.id)
        checkpoint = NavigationCheckpoint.objects.get(work=row)
        if row.generation != unit.generation or checkpoint.pending_unit != unit.unit_key:
            raise SupersededAttempt
        return row, checkpoint

    def _receipt(
        self,
        row: NavigationWork,
        unit: NavigationUnit,
        *,
        pages: int = 0,
        details: int = 0,
        reason: str = "round_robin",
    ) -> None:
        observations = (
            list(
                ListingObservation.objects.filter(
                    cycle=row.cycle,
                    listing__external_id=unit.target.external_id if unit.target else "",
                ).values_list("id", flat=True)
            )
            if details
            else []
        )
        NavigationUnitReceipt.objects.create(
            work=row,
            unit_key=unit.unit_key,
            input_revision=unit.revision,
            generation=unit.generation,
            confirmed_at=self._clock(),
            turn_order=row.last_turn,
            consumed_pages=pages,
            consumed_details=details,
            reason=reason,
            observation_ids=[str(identity) for identity in observations],
        )

    def _pending_ids(self, attempt: Attempt, query_key: str) -> set[str]:
        return {
            target.external_id
            for target in self._collection.detail_targets(attempt)
            if any(f"marketplace:{match.kind}:{match.key}" == query_key for match in target.matches)
        }

    def _stage_page(
        self,
        attempt: Attempt,
        unit: NavigationUnit,
        row: NavigationWork,
        checkpoint: NavigationCheckpoint,
        page: Page,
    ) -> None:
        pending = self._pending_ids(attempt, unit.query.key)
        candidates = tuple(
            candidate
            for candidate in page.candidates
            if unit.query.interest.kind == "category"
            or candidate.evidence.title is None
            or unit.query.matches_title(candidate.evidence.title)
        )
        repeated = tuple(candidate for candidate in candidates if candidate.external_id in pending)
        fresh = tuple(candidate for candidate in candidates if candidate.external_id not in pending)
        capacity = max(0, self._policy.pending_details - len(pending))
        self._collection.stage(attempt, unit.query.key, (*repeated, *fresh[:capacity]))
        checkpoint.buffered_candidates = [
            encode_candidate(candidate) for candidate in fresh[capacity:]
        ]
        if checkpoint.buffered_candidates:
            row.reason = "pending_details_limit"

    def _drain_buffers(self, attempt: Attempt, scope: Scope) -> None:
        queries = {query.key: query for query in scope.searches}
        checkpoints = (
            NavigationCheckpoint.objects.filter(work__cycle_id=attempt.cycle_id)
            .exclude(buffered_candidates=[])
            .select_related("work")
        )
        for checkpoint in checkpoints:
            self._drain_one(attempt, checkpoint, queries[checkpoint.work.origin_interest])

    def _drain_one(
        self, attempt: Attempt, checkpoint: NavigationCheckpoint, query: "Search"
    ) -> None:
        capacity = max(0, self._policy.pending_details - len(self._pending_ids(attempt, query.key)))
        if capacity == 0:
            return
        candidates = tuple(
            decode_candidate(item) for item in checkpoint.buffered_candidates[:capacity]
        )
        self._collection.stage(attempt, query.key, candidates)
        checkpoint.buffered_candidates = checkpoint.buffered_candidates[capacity:]
        if not checkpoint.buffered_candidates:
            row = checkpoint.work
            unit = to_unit(row, checkpoint, query, None)
            self._advance_term(
                attempt,
                unit,
                row,
                checkpoint,
                Page((), checkpoint.cursor, window_proof=checkpoint.buffer_proof),
            )
            row.reason = ""
            row.save()
        checkpoint.save()

    @transaction.atomic
    def page(self, attempt: Attempt, unit: NavigationUnit, page: Page) -> None:
        row, checkpoint = self._owned(attempt, unit)
        if NavigationUnitReceipt.objects.filter(
            work=row, unit_key=unit.unit_key, input_revision=unit.revision
        ).exists():
            return
        if page.diagnostic:
            self.failed(attempt, unit, SourceFailure(page.diagnostic))
            return
        signature = (
            str(checkpoint.term_index)
            + ":"
            + hashlib.sha256(
                ",".join(sorted(item.external_id for item in page.candidates)).encode()
            ).hexdigest()
        )
        replay = signature in checkpoint.signatures and page.candidates
        if replay and row.reason != "cursor_rebuilt":
            self.failed(attempt, unit, SourceFailure("repeated_page"))
            return
        if page.continuation is not None and page.continuation == unit.cursor:
            self.failed(attempt, unit, SourceFailure("repeated_continuation"))
            return
        self._stage_page(attempt, unit, row, checkpoint, page)
        checkpoint.invalid_cards += page.invalid_cards
        checkpoint.buffer_proof = page.window_proof
        checkpoint.pages += page.traversed_pages
        checkpoint.signatures.append(signature)
        checkpoint.cursor = page.continuation
        row.phase, row.reason, row.failures = "pending", "", 0
        total_pages = (
            NavigationCheckpoint.objects.filter(
                work__cycle_id=attempt.cycle_id,
                work__origin_interest=row.origin_interest,
                work__front="discovery",
            )
            .exclude(work=row)
            .aggregate(total=Sum("pages"))["total"]
            or 0
        )
        if (
            checkpoint.pages + total_pages
            >= int(checkpoint.limits.get("cycle_pages", self._policy.cycle_pages))
            and page.continuation
        ):
            row.phase, row.reason = "partial", "window_limit"
            self._collection.record(attempt, unit.query.key, SourceFailure("window_limit"))
        else:
            self._advance_term(
                attempt, unit, row, checkpoint, page
            ) if not checkpoint.buffered_candidates else None
        row.last_progress_at = row.last_progress_at if replay else self._clock()
        row.next_attempt_at = None
        checkpoint.save()
        row.save()
        self._receipt(
            row,
            unit,
            pages=page.traversed_pages,
            reason="cursor_rebuilt" if page.rebuilt else "round_robin",
        )

    def _advance_term(
        self,
        attempt: Attempt,
        unit: NavigationUnit,
        row: NavigationWork,
        checkpoint: NavigationCheckpoint,
        page: Page,
    ) -> None:
        if page.continuation is not None:
            return
        checkpoint.term_index += 1
        if checkpoint.term_index < len(checkpoint.terms):
            return
        checkpoint.term_index -= 1
        row.phase = "complete"
        self._collection.record(
            attempt,
            unit.query.key,
            SourceFailure("unverified_identity") if checkpoint.invalid_cards else None,
            None if checkpoint.invalid_cards else page.window_proof or "source_exhausted",
        )

    @transaction.atomic
    def detail(self, attempt: Attempt, unit: NavigationUnit, candidate: Candidate) -> None:
        row, checkpoint = self._owned(attempt, unit)
        if NavigationUnitReceipt.objects.filter(
            work=row, unit_key=unit.unit_key, input_revision=unit.revision
        ).exists():
            return
        assert unit.target is not None
        if candidate.external_id != unit.target.external_id:
            self._failure(row, checkpoint, SourceFailure("unverified_identity"))
            return
        self._collection.stage(
            attempt, unit.unit_key, (replace(candidate, matches=unit.target.matches),)
        )
        self._collection.record(attempt, unit.unit_key, None)
        while self._collection.publish_batch(attempt, ready_only=True):
            pass
        checkpoint.details += 1
        checkpoint.pending_unit = ""
        checkpoint.save()
        row.phase, row.reason, row.failures = "pending", "", 0
        row.last_progress_at, row.next_attempt_at = self._clock(), None
        row.save()
        NavigationWork.objects.filter(cycle_id=attempt.cycle_id, front="investigation").update(
            failures=0
        )
        self._receipt(row, unit, details=1)

    @transaction.atomic
    def failed(self, attempt: Attempt, unit: NavigationUnit, failure: SourceFailure) -> bool:
        row, checkpoint = self._owned(attempt, unit)
        if NavigationUnitReceipt.objects.filter(
            work=row, unit_key=unit.unit_key, input_revision=unit.revision
        ).exists():
            raise SupersededAttempt

        self._failure(row, checkpoint, failure)
        NavigationUnitReceipt.objects.get_or_create(
            work=row,
            unit_key=unit.unit_key + ":failed:" + str(unit.generation),
            input_revision=unit.revision,
            defaults=dict(
                generation=unit.generation,
                confirmed_at=self._clock(),
                turn_order=row.last_turn,
                consumed_pages=int(unit.target is None),
                consumed_details=int(unit.target is not None),
                reason=failure.reason,
            ),
        )
        if unit.target is not None and not failure.access and not failure.retry_after:
            self._collection.record(attempt, "detail:" + unit.target.external_id, failure)
            row.phase, row.next_attempt_at = "pending", None
            streak = row.failures
            NavigationWork.objects.filter(cycle_id=attempt.cycle_id, front="investigation").update(
                failures=streak
            )
            if row.failures >= 3:
                row.phase, row.reason = "partial", "detail_failures_pause"
                NavigationWork.objects.filter(cycle_id=attempt.cycle_id).exclude(
                    phase="complete"
                ).update(phase="partial", reason="detail_failures_pause")
                self._collection.record(
                    attempt,
                    "source_health",
                    SourceFailure("detail_failures_pause", self._collection_policy.retry_base),
                )
            row.save()
        if failure.retry_after:
            self._source_wait(attempt, failure.retry_after)
            NavigationWork.objects.filter(cycle_id=attempt.cycle_id).exclude(
                phase__in=["complete", "partial"]
            ).update(next_attempt_at=row.next_attempt_at, reason=failure.reason, phase="waiting")
        if unit.target is None or failure.access:
            self._collection.record(attempt, unit.query.key, failure)
        if failure.access:
            CollectionState.objects.filter(current_id=attempt.cycle_id).update(
                access_suspended=True
            )
            NavigationWork.objects.filter(cycle_id=attempt.cycle_id).exclude(
                phase="complete"
            ).update(phase="suspended", reason=failure.reason)

        return (
            failure.access
            or failure.retry_after > 0
            or (unit.target is not None and row.failures >= 3)
        )

    def _source_wait(self, attempt: Attempt, seconds: int) -> None:
        state = CollectionState.objects.get(current_id=attempt.cycle_id)
        deadline = self._clock() + timedelta(seconds=seconds)
        state.source_not_before = max(state.source_not_before or deadline, deadline)
        state.next_attempt_at = max(state.next_attempt_at or deadline, deadline)
        state.save(update_fields=["source_not_before", "next_attempt_at"])

    def _failure(
        self, row: NavigationWork, checkpoint: NavigationCheckpoint, failure: SourceFailure
    ) -> None:
        row.failures += 1
        row.reason = failure.reason
        row.phase = "suspended" if failure.access else "waiting"
        if failure.reason in {
            "repeated_page",
            "repeated_continuation",
            "wrong_search_query",
            "wrong_category_context",
            "search_context_unverified",
            "wrong_context",
            "wrong_search_context",
        }:
            row.phase = "partial"
        row.next_attempt_at = self._clock() + timedelta(
            seconds=max(
                failure.retry_after,
                min(
                    self._collection_policy.retry_max,
                    self._collection_policy.retry_base * 2 ** min(row.failures - 1, 5),
                ),
            )
        )
        if failure.reason in {"continuation_scope_mismatch", "cursor_expired"}:
            checkpoint.cursor = None
            row.reason = "cursor_rebuilt"
        checkpoint.save()
        row.save()

    @transaction.atomic
    def yield_slice(self, attempt: Attempt, scope: Scope) -> None:
        cycle = self._guard(attempt, scope.revision, allow_blocked=True)
        if cycle.state.access_suspended or (
            cycle.state.source_not_before and cycle.state.source_not_before > self._clock()
        ):
            self._finish_cycle(attempt, cycle)
            return
        units = self._eligible_units(attempt, scope, self._policy.slice_pages, True)
        if select_turn(tuple(unit.turn for unit in units), self._clock()) is None:
            self._finish_cycle(attempt, cycle)
            return
        self._enqueue(attempt, 0)

    def _finish_cycle(self, attempt: Attempt, cycle: CollectionCycle) -> None:
        self._persist_pending(attempt)
        NavigationWork.objects.filter(cycle=cycle, front="investigation", failures=0).exclude(
            phase="partial"
        ).update(phase="complete")
        self._collection.mark_scanned(attempt, Point(**cycle.origin) if cycle.origin else None)
        cycle.refresh_from_db()
        interrupted = any(
            result and (result["access"] or result["retry_after"])
            for result in cycle.results.values()
        )
        while self._collection.publish_batch(attempt, ready_only=interrupted):
            pass
        self._collection.finish(attempt, self._collection_policy)
        cycle.refresh_from_db()
        state = CollectionState.objects.get(current_id=cycle.id)
        NavigationWork.objects.filter(cycle=cycle, phase="pending", failures__gt=0).update(
            phase="waiting"
        )
        NavigationWork.objects.filter(cycle=cycle, phase__in=["waiting", "partial"]).update(
            next_attempt_at=state.next_attempt_at
        )

    def _persist_pending(self, attempt: Attempt) -> None:
        # Unconfirmed detail inputs survive F04 cleanup in the same commit as
        # partial publication/finish. Previous receipts and windows are immutable.
        from garimpei.infra.persistence.listing_models import CollectionCandidate

        for row in NavigationWork.objects.filter(
            cycle_id=attempt.cycle_id, front="investigation", purpose="active"
        ):
            checkpoint = NavigationCheckpoint.objects.get(work=row)
            staged = [
                item
                for values in CollectionCandidate.objects.filter(
                    cycle_id=attempt.cycle_id, query_key=row.origin_interest
                ).values_list("candidates", flat=True)
                for item in values
            ]
            records = {str(item): item for item in [*checkpoint.buffered_candidates, *staged]}
            checkpoint.buffered_candidates = list(records.values())
            checkpoint.save()

    @transaction.atomic
    def resume(self, identity: UUID, revision: int) -> None:
        lock_monitoring_publication()
        row = NavigationWork.objects.select_related("cycle__state").filter(id=identity).first()
        if row is None:
            raise MissingNavigation
        snapshot = self._configuration.execute()
        if (
            snapshot.revision != revision
            or row.revision != revision
            or row.cycle.state.access_suspended
        ):
            raise StaleNavigation
        if row.cycle.state.current_id != row.cycle_id or (
            row.cycle.state.source_not_before and row.cycle.state.source_not_before > self._clock()
        ):
            raise StaleNavigation
        row.phase, row.reason, row.next_attempt_at = (
            "pending",
            "resume_requested",
            self._clock(),
        )
        row.save(update_fields=["phase", "reason", "next_attempt_at"])
        if row.cycle.finished_at:
            CollectionState.objects.filter(current_id=row.cycle_id).update(
                next_attempt_at=self._clock()
            )
            self._collection.reconcile(self._collection_policy)
            return
        self._enqueue(Attempt(row.cycle_id, row.cycle.state.generation), 0)

    @transaction.atomic
    def request_research(
        self,
        request_id: UUID,
        revision: int,
        interest: str,
        term: str,
        purpose: str,
        constraints: str,
    ) -> UUID:
        lock_monitoring_publication()
        scope = Scope.from_snapshot(self._configuration.execute())
        if (
            scope is None
            or scope.revision != revision
            or scope.key != constraints
            or purpose not in {"attributes", "comparables"}
        ):
            raise StaleNavigation
        query = next((query for query in scope.searches if query.key == interest), None)
        if query is None or not self._catalog.permits(query.term, term):
            raise StaleNavigation
        expected_context = hashlib.sha256(
            f"{scope.key}:{revision}:{interest}:{term}:{purpose}".encode()
        ).hexdigest()
        previous = NavigationWork.objects.filter(request_id=request_id).first()
        if previous:
            if (
                previous.revision != revision
                or previous.original_term != term
                or previous.origin_interest != interest
                or NavigationCheckpoint.objects.get(work=previous).context.get("request_hash")
                != expected_context
            ):
                raise StaleNavigation
            return previous.id
        state = CollectionState.objects.filter(
            configuration_id=scope.configuration_id, source=scope.source
        ).first()
        if (
            state is None
            or state.current_id is None
            or state.current is None
            or state.current.finished_at
            or state.current.revision != revision
            or state.current.scope_key != scope.key
        ):
            raise StaleNavigation
        limits = self._cycle_limits(state.current.id)
        all_terms = {
            term
            for values in NavigationCheckpoint.objects.filter(
                work__cycle=state.current, work__origin_interest=interest
            ).values_list("terms", flat=True)
            for term in values
        }
        if term not in all_terms and len(all_terms) >= limits["cycle_terms"]:
            raise StaleNavigation
        row = NavigationWork.objects.create(
            cycle=state.current,
            configuration_id=scope.configuration_id,
            source=scope.source,
            scope_key=scope.key,
            revision=revision,
            origin_interest=interest,
            original_term=term,
            front="discovery",
            purpose="research",
            request_id=request_id,
            last_turn=(
                NavigationWork.objects.filter(
                    cycle=state.current, origin_interest=interest, front="discovery"
                ).aggregate(last=Max("last_turn"))["last"]
                or 0
            ),
        )
        NavigationCheckpoint.objects.create(
            work=row,
            catalog_version=self._catalog.version,
            context_hash=hashlib.sha256(
                f"{expected_context}:{state.current.window_start.isoformat() if state.current.window_start else None}:{state.current.window_end.isoformat() if state.current.window_end else None}".encode()
            ).hexdigest(),
            terms=[term],
            limits=limits,
            context={
                "purpose": purpose,
                "request_hash": expected_context,
                "window_start": state.current.window_start.isoformat()
                if state.current.window_start
                else None,
                "window_end": state.current.window_end.isoformat()
                if state.current.window_end
                else None,
            },
        )
        return row.id
