from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from django.db import transaction
from django.db.models import Q

from garimpei.domain.operations.ports import ProgressRecorder
from garimpei.domain.valuation.identification_values import IdentificationResult
from garimpei.domain.valuation.ports import WorkInput
from garimpei.domain.valuation.values import Comparable, Valuation
from garimpei.infra.persistence.identity_models import ManualIdentityRevision
from garimpei.infra.persistence.listing_models import Listing, ListingObservation
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.infra.persistence.valuation_models import (
    ValuationEvaluation,
    ValuationProgress,
    ValuationWork,
)
from garimpei.infra.repository.alert.first_inputs import invalidate_first_alert
from garimpei.infra.repository.valuation.identity_mapper import identify_row
from garimpei.infra.repository.valuation.mapper import (
    decode_comparable,
    decode_valuation,
    encode_comparable,
    encode_valuation,
    listing_comparable,
    mapping,
    records,
    valuation_signature,
)


@dataclass(frozen=True)
class PendingRequest:
    listing_id: UUID
    snapshot: dict[str, object]
    signature: str


class PostgresValuationRepository:
    def __init__(
        self, enqueue: Callable[[UUID], int], operations: ProgressRecorder | None = None
    ) -> None:
        self._enqueue = enqueue
        self._operations = operations

    def reconcile(self, now: datetime) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            snapshots = tuple(
                row
                for row in Listing.objects.select_related(
                    "latest", "identity_progress__manual__observation"
                ).order_by("id")
                if row.latest is not None and row.latest.observed_at <= now
            )
            watermark = (ListingObservation.objects.count(), ManualIdentityRevision.objects.count())
            progress = {p.listing_id: p for p in ValuationProgress.objects.all()}
            pending = set(
                ValuationWork.objects.filter(completed=False, next_attempt_at__lte=now)
                .filter(Q(lease_until=None) | Q(lease_until__lte=now))
                .values_list("listing_id", flat=True)
            )
        # All related observation/manual rows above are eagerly captured immutable inputs.
        # Identity parsing and matching run outside the collection publication transaction.
        rows = tuple(
            _listing(row, identify_row(row, getattr(row, "identity_progress", None)))
            for row in snapshots
        )
        requests = self._requests(rows, progress, pending, now)
        for offset in range(0, len(requests), 10):
            if not self._request_batch(requests[offset : offset + 10], watermark, now):
                return

    def _requests(
        self,
        rows: tuple[Comparable, ...],
        progress: dict[UUID, ValuationProgress],
        pending: set[UUID],
        now: datetime,
    ) -> tuple[PendingRequest, ...]:
        products = {row.listing_id: row.product for row in rows}
        groups: dict[str, list[Comparable]] = defaultdict(list)
        for row in rows:
            product = products[row.listing_id]
            if product is not None:
                groups[product].append(row)
        requests = []
        for row in rows:
            product = products[row.listing_id]
            candidates = tuple(
                c for c in groups.get(product or "", ()) if c.listing_id != row.listing_id
            )
            request = self._input(row, product, candidates)
            current = progress.get(row.listing_id)
            if (
                current is None
                or current.signature != request.signature
                or (current.due_at is not None and current.due_at < now)
                or row.listing_id in pending
            ):
                requests.append(request)
        return tuple(requests)

    @staticmethod
    def _input(
        target: Comparable, product: str | None, candidates: tuple[Comparable, ...]
    ) -> PendingRequest:
        snapshot: dict[str, object] = dict(
            target=encode_comparable(target),
            candidates=[encode_comparable(row) for row in candidates],
        )
        signature = valuation_signature(snapshot, product)
        return PendingRequest(target.listing_id, snapshot, signature)

    def _request_batch(
        self, requests: tuple[PendingRequest, ...], watermark: tuple[int, int], now: datetime
    ) -> bool:
        with transaction.atomic():
            lock_monitoring_publication()
            # Both histories are append-only. A manual edit also fences every remaining batch,
            # even when no new listing observation was published while analysis was running.
            if (
                ListingObservation.objects.count(),
                ManualIdentityRevision.objects.count(),
            ) != watermark:
                return False
            for request in requests:
                self._request(request, now)
            return True

    def _request(self, request: PendingRequest, now: datetime) -> None:
        progress, _ = ValuationProgress.objects.get_or_create(listing_id=request.listing_id)
        if progress.signature != request.signature or (
            progress.due_at is not None and progress.due_at < now
        ):
            if (
                self._operations is not None
                and ValuationWork.objects.filter(completed=False).count() >= 1000
            ):
                return
            progress.requested += 1
            progress.signature = request.signature
            progress.due_at = None
            progress.save()
            ValuationWork.objects.create(
                listing_id=request.listing_id,
                revision=progress.requested,
                snapshot=request.snapshot,
                requested_at=now,
                next_attempt_at=now,
            )
        pending = ValuationWork.objects.filter(
            listing_id=request.listing_id,
            revision=progress.requested,
            completed=False,
            next_attempt_at__lte=now,
        ).first()
        if pending is not None and (pending.lease_until is None or pending.lease_until <= now):
            if self._operations is not None and not self._operations.admits(
                "valuation", str(pending.listing_id), pending.revision, now
            ):
                return
            pending.lease_until = now + timedelta(seconds=60)
            pending.attempts += 1
            pending.save(update_fields=["lease_until", "attempts"])
            self._enqueue(pending.id)

    def work(self, identity: UUID) -> WorkInput | None:
        work = ValuationWork.objects.filter(id=identity, completed=False).first()
        if work is None:
            return None
        progress = ValuationProgress.objects.select_related("current").get(
            listing_id=work.listing_id
        )
        if progress.requested != work.revision:
            return None
        raw = mapping(work.snapshot)
        previous = (
            decode_valuation(mapping(progress.current.result)).new if progress.current else None
        )
        return WorkInput(
            work.id,
            work.listing_id,
            work.revision,
            decode_comparable(mapping(raw["target"])),
            tuple(decode_comparable(row) for row in records(raw["candidates"])),
            previous,
        )

    def publish(self, work: WorkInput, value: Valuation, due: datetime) -> None:
        with transaction.atomic():
            lock_monitoring_publication()
            row = ValuationWork.objects.select_for_update().get(id=work.id)
            if row.completed:
                return
            progress = ValuationProgress.objects.select_for_update().get(listing_id=work.listing_id)
            latest = Listing.objects.select_related(
                "latest", "identity_progress__manual__observation"
            ).get(id=work.listing_id)
            current_identity = identify_row(latest, getattr(latest, "identity_progress", None))
            input_changed = latest.latest is None or latest.latest.ordinal != work.target.revision
            identity_changed = work.target.identification is not None and (
                work.target.identification.manual_revision,
                work.target.identification.state,
                work.target.identification.product_key,
            ) != (
                current_identity.manual_revision,
                current_identity.state,
                current_identity.product_key,
            )
            if progress.requested != work.revision or input_changed or identity_changed:
                row.completed = True
                row.save(update_fields=["completed"])
                return
            evaluation = ValuationEvaluation.objects.create(
                id=value.id, work=row, result=encode_valuation(value)
            )
            progress.current = evaluation
            progress.due_at = due
            progress.save(update_fields=["current", "due_at"])
            invalidate_first_alert(work.listing_id, value.evaluated_at)
            row.completed, row.diagnostic = True, ""
            row.save(update_fields=["completed", "diagnostic"])
            if self._operations:
                self._operations.confirm(
                    "valuation",
                    str(work.listing_id),
                    work.revision,
                    str(value.id),
                    value.evaluated_at,
                )

    def failed(self, identity: UUID, now: datetime) -> None:
        self._record_failure(identity, now)
        ValuationWork.objects.filter(id=identity, completed=False).update(
            diagnostic="valuation_publication_failed",
            lease_until=None,
            next_attempt_at=now + timedelta(seconds=5),
        )

    def _record_failure(self, identity: UUID, now: datetime) -> None:
        row = ValuationWork.objects.filter(id=identity, completed=False).first()
        if row is not None and self._operations:
            self._operations.failure(
                "valuation", str(row.listing_id), row.revision, "valuation_publication_failed", now
            )


def _listing(row: Listing, identification: IdentificationResult | None = None) -> Comparable:
    return listing_comparable(row, identification)
