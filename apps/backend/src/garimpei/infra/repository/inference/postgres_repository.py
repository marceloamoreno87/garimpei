from collections.abc import Callable
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import cast
from uuid import UUID

from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now as clock_now

from garimpei.domain.inference.errors import RECOVERABLE, InferenceError
from garimpei.domain.inference.ports import AnalysisTicket, AnalysisWork, PreparedPart
from garimpei.domain.inference.request import AnalysisInput
from garimpei.infra.persistence.inference_models import (
    InferenceControl,
    InferencePart,
    InferenceRequest,
)
from garimpei.infra.persistence.listing_models import Listing, ListingObservation


class PostgresInferenceRepository:
    def __init__(
        self,
        enqueue: Callable[[], int],
        queue_limit: int,
        lease: int = 240,
        reserve: Callable[[str], None] | None = None,
    ) -> None:
        self._enqueue, self._queue_limit, self._lease = enqueue, queue_limit, lease
        self._reserve = reserve

    def admit(
        self, value: AnalysisInput, artifact: str, parts: tuple[PreparedPart, ...]
    ) -> AnalysisTicket:
        with transaction.atomic():
            _control()
            signature = value.signature(artifact)
            existing = InferenceRequest.objects.filter(signature=signature).first()
            if existing is not None:
                return AnalysisTicket(existing.id, existing.state, True)
            return self._admit_new(value, artifact, parts, signature)

    def _admit_new(
        self, value: AnalysisInput, artifact: str, parts: tuple[PreparedPart, ...], signature: str
    ) -> AnalysisTicket:
        observation = ListingObservation.objects.filter(pk=value.observation_id).first()
        if observation is None or observation.ordinal != value.revision:
            raise InferenceError("observation_revision_mismatch", 409)
        listing = Listing.objects.select_for_update().get(pk=observation.listing_id)
        if listing.latest_id != observation.id:
            raise InferenceError("superseded", 409)
        if (
            InferenceRequest.objects.filter(
                state__in=["pending", "running", "awaiting_resource", "paused"]
            ).count()
            >= self._queue_limit
        ):
            raise InferenceError("queue_full", 409)
        if self._reserve is not None:
            self._reserve(signature)
        row = InferenceRequest.objects.create(
            observation=observation,
            revision=value.revision,
            signature=signature,
            artifact=artifact,
            prompt_version=value.prompt_version,
            schema_version=value.schema_version,
            created_at=clock_now(),
            coverage=[entry for part in parts for entry in part.coverage],
        )
        InferencePart.objects.bulk_create(
            [
                InferencePart(
                    request=row,
                    position=index,
                    content=asdict(part) | {"model_digest": part.model_digest},
                )
                for index, part in enumerate(parts)
            ]
        )
        transaction.on_commit(self._enqueue)
        return AnalysisTicket(row.id, row.state, False)

    def claim(self, now: datetime) -> AnalysisWork | None:
        with transaction.atomic():
            control = _control()
            if (
                control.paused
                or control.active_request
                or control.reason in {"execution_unknown", "unload_failed"}
            ):
                return None
            row = (
                InferenceRequest.objects.select_for_update()
                .filter(
                    state__in=["pending", "awaiting_resource"],
                )
                .filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now))
                .order_by("created_at")
                .first()
            )
            if row is None:
                return None
            return self._claim_row(row, control, now)

    def _claim_row(
        self, row: InferenceRequest, control: InferenceControl, now: datetime
    ) -> AnalysisWork | None:
        if not _current(row):
            row.state = "superseded"
            row.save(update_fields=["state"])
            return None
        part = (
            InferencePart.objects.select_for_update()
            .filter(request=row, state="pending")
            .order_by("position")
            .first()
        )
        if part is None:
            return None
        control.generation += 1
        control.active_request, control.lease_until = row.id, now + timedelta(seconds=self._lease)
        control.reason = "running"
        control.save()
        row.state = "running"
        row.save(update_fields=["state"])
        part.state, part.generation = "running", control.generation
        part.attempts += 1
        part.save()
        return AnalysisWork(
            row.id,
            control.generation,
            part.pk,
            row.artifact,
            decode_part(cast(dict[str, object], part.content)),
        )

    def authorize(self, work: AnalysisWork) -> bool:
        with transaction.atomic():
            control = _control()
            if not _owns(control, work):
                return False
            if not control.paused:
                return True
            part = InferencePart.objects.select_for_update().get(pk=work.part_id)
            part.state, part.attempts = "pending", max(0, part.attempts - 1)
            part.save(update_fields=["state", "attempts"])
            InferenceRequest.objects.filter(pk=work.request_id).update(state="pending")
            control.active_request, control.lease_until = None, None
            control.reason = "paused"
            control.save()
            return False

    def publish(
        self,
        work: AnalysisWork,
        payload: dict[str, object],
        metrics: dict[str, object],
        now: datetime,
    ) -> bool:
        with transaction.atomic():
            control = _control()
            row = InferenceRequest.objects.select_for_update().get(pk=work.request_id)
            if not _owns(control, work):
                return False
            part = InferencePart.objects.select_for_update().get(pk=work.part_id)
            part.result, part.metrics = payload, metrics | {"sent": True}
            part.state = "succeeded"
            part.reason = ""
            part.save()
            current = _current(row, lock=True)
            row.state = (
                "pending"
                if InferencePart.objects.filter(request=row, state="pending").exists()
                else "succeeded"
            )
            if not current:
                row.state = "superseded"
            row.completed_at = now if row.state in {"succeeded", "superseded"} else None
            row.reason = ""
            row.save()
            control.active_request, control.lease_until = None, None
            control.last_used_at, control.resident, control.reason = (
                now,
                True,
                "paused" if control.paused else "ready",
            )
            control.save()
            return current

    def failed(self, work: AnalysisWork, code: str, now: datetime, *, sent: bool = False) -> None:
        with transaction.atomic():
            control = _control()
            if not _owns(control, work):
                return
            row = InferenceRequest.objects.select_for_update().get(pk=work.request_id)
            part = InferencePart.objects.select_for_update().get(pk=work.part_id)
            part.metrics = dict(part.metrics, sent=sent or part.metrics.get("sent", False))
            recoverable = code in RECOVERABLE and part.attempts < 3
            row.state, row.reason = ("awaiting_resource" if recoverable else "failed"), code
            row.next_attempt_at = (
                now + timedelta(seconds=15 * part.attempts) if recoverable else None
            )
            row.save()
            part.state, part.reason = ("pending" if recoverable else "failed"), code
            if code in {"timeout", "execution_unknown"}:
                part.state = "running"
            part.save()
            control.reason = code
            if code not in {"timeout", "execution_unknown"}:
                control.active_request, control.lease_until = None, None
            else:
                control.reason = "execution_unknown"
                row.state = "awaiting_resource"
                row.save(update_fields=["state"])
            control.save()

    def control(self, paused: bool, revision: int) -> None:
        with transaction.atomic():
            control = _control()
            if control.paused == paused:
                return
            if control.revision != revision:
                raise InferenceError("control_conflict", 409)
            control.paused = paused
            control.revision += 1
            if control.active_request is None:
                control.reason = (
                    "paused" if paused else "ready" if control.service else "service_unavailable"
                )
            control.save(update_fields=["paused", "revision", "reason"])

    def reconcile(self, now: datetime) -> None:
        with transaction.atomic():
            control = _control()
            if control.active_request and control.lease_until and control.lease_until <= now:
                control.reason = "execution_unknown"
                control.save(update_fields=["reason"])
                return
            InferenceRequest.objects.filter(
                state="awaiting_resource", next_attempt_at__lte=now
            ).update(next_attempt_at=None)
            if (
                not control.paused
                and not control.active_request
                and control.reason not in {"execution_unknown", "unload_failed"}
                and InferenceRequest.objects.filter(
                    state__in=["pending", "awaiting_resource"], next_attempt_at__isnull=True
                ).exists()
            ):
                transaction.on_commit(self._enqueue)

    def record_diagnostic(self, value: dict[str, object], now: datetime) -> None:
        with transaction.atomic():
            control = _control()
            control.service = value.get("service") is True
            control.resident = value.get("resident") is True
            control.checked_at = now
            control.artifact = str(value.get("artifact", ""))
            if control.active_request is None and control.reason not in {
                "execution_unknown",
                "unload_failed",
            }:
                control.reason = str(value.get("reason", "service_unavailable"))
            control.save()

    def unloaded(self, confirmed: bool, now: datetime) -> None:
        with transaction.atomic():
            control = _control()
            if control.active_request:
                return
            control.resident = not confirmed
            control.checked_at = now
            control.reason = (
                ("paused" if control.paused else "idle_unloaded") if confirmed else "unload_failed"
            )
            control.save()

    def recovered(self, confirmed: bool, now: datetime) -> None:
        with transaction.atomic():
            control = _control()
            if not confirmed or control.reason not in {"execution_unknown", "unload_failed"}:
                return
            _recover_parts(control.active_request, now)
            control.active_request, control.lease_until = None, None
            control.generation += 1
            control.resident, control.reason = False, "idle_unloaded"
            control.save()


def _recover_parts(identity: UUID | None, now: datetime) -> None:
    if identity is None:
        return
    row = InferenceRequest.objects.select_for_update().get(pk=identity)
    part = InferencePart.objects.select_for_update().filter(request=row, state="running").first()
    if part is None:
        row.state, row.reason, row.next_attempt_at = "failed", "invalid_recovery_state", None
    elif part.attempts >= 3:
        part.state = "failed"
        part.save(update_fields=["state"])
        row.state, row.next_attempt_at = "failed", None
    else:
        part.state = "pending"
        part.save(update_fields=["state"])
        row.state = "awaiting_resource"
        row.next_attempt_at = now + timedelta(seconds=15 * part.attempts)
    row.save(update_fields=["state", "reason", "next_attempt_at"])


def _control() -> InferenceControl:
    InferenceControl.objects.get_or_create(pk=1)
    return InferenceControl.objects.select_for_update().get(pk=1)


def _owns(control: InferenceControl, work: AnalysisWork) -> bool:
    return control.active_request == work.request_id and control.generation == work.generation


def _current(row: InferenceRequest, *, lock: bool = False) -> bool:
    listing_id = ListingObservation.objects.get(pk=row.observation_id).listing_id
    query = Listing.objects.select_for_update() if lock else Listing.objects
    current = query.filter(pk=listing_id, latest_id=row.observation_id).exists()
    newer = InferenceRequest.objects.filter(
        observation_id=row.observation_id, created_at__gt=row.created_at
    ).exists()
    return current and not newer


def decode_part(value: dict[str, object]) -> PreparedPart:
    return PreparedPart(
        str(value["key"]),
        str(value["text"]),
        str(value["image_id"]) if value["image_id"] else None,
        str(value["image_hash"]) if value["image_hash"] else None,
        tuple(cast(list[dict[str, object]], value["coverage"])),
        str(value.get("model_digest", "")),
    )
