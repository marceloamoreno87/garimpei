import hashlib
from dataclasses import fields
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from django.db import transaction

from garimpei.domain.operations.errors import OperationsError
from garimpei.domain.operations.progress import OperationalProgress, ProgressConflict
from garimpei.infra.persistence.operations_models import (
    BackupSchedule,
    OperationalDiagnostic,
    OperationalUnit,
    RecoveryBarrier,
)


class PostgresOperationalRepository:
    def __init__(self, installation: str, clock: "Callable[[], datetime]") -> None:
        self._installation, self._clock = installation, clock

    def confirm(
        self, stage: str, key: str, revision: int, boundary: str, now: datetime, *, pending: int = 0
    ) -> None:
        with transaction.atomic():
            row = self._row(stage, key, revision, now)
            state = restore_progress(row)
            state.attempt(now)
            state.confirm(boundary, generation=row.generation, revision=revision, now=now)
            if not state.failures:
                state.pending = pending
            _save(row, state)

    def complete(self, stage: str, key: str, revision: int, now: datetime) -> None:
        with transaction.atomic():
            row = self._row(stage, key, revision, now)
            row.last_attempt_at, row.pending = now, 0
            row.reason = "no_new_frontier"
            row.save(update_fields=["last_attempt_at", "pending", "reason"])

    def failure(
        self,
        stage: str,
        key: str,
        revision: int,
        reason: str,
        now: datetime,
        *,
        retry_after: int = 0,
    ) -> None:
        with transaction.atomic():
            row = self._row(stage, key, revision, now)
            state = restore_progress(row)
            state.pending = 1
            state.fail(reason, now)
            state.wait_until(
                now + timedelta(seconds=max(retry_after, min(300, 15 * 2**state.failures))), reason
            )
            _save(row, state)
            OperationalDiagnostic.objects.create(
                id=uuid4(), unit=row, reason=reason, created_at=now
            )

    def admits(self, stage: str, key: str, revision: int, now: datetime) -> bool:
        row = OperationalUnit.objects.filter(
            installation=self._installation, stage=stage, key=_unit_key(key), revision=revision
        ).first()
        return (
            row is None
            or (not row.suspended and row.pending == 0)
            or restore_progress(row).admits(now)
        )

    def _row(self, stage: str, key: str, revision: int, now: datetime) -> OperationalUnit:
        state = OperationalProgress.create(stage, key, revision=revision, now=now)
        row, _ = OperationalUnit.objects.get_or_create(
            installation=self._installation,
            stage=stage,
            key=_unit_key(key),
            revision=revision,
            defaults={"id": state.id, "pending_since": now, "scope": key[:512]},
        )
        return OperationalUnit.objects.select_for_update().get(id=row.id)

    def resume(self, identity: UUID, stage: str, revision: int) -> None:
        with transaction.atomic():
            row = (
                OperationalUnit.objects.select_for_update()
                .filter(id=identity, installation=self._installation, stage=stage)
                .first()
            )
            if row is None:
                raise OperationsError("operational_unit_unknown", 404)
            if RecoveryBarrier.objects.filter(
                installation=self._installation, state="blocked"
            ).exists():
                raise OperationsError("recovery_barrier")
            state = restore_progress(row)
            try:
                state.resume(expected_revision=revision, now=self._clock())
            except ProgressConflict:
                raise OperationsError("operational_revision_or_access_conflict") from None
            _save(row, state)
            OperationalDiagnostic.objects.create(
                id=uuid4(), unit=row, reason="explicit_resume", created_at=self._clock()
            )
            if row.stage == "maintenance" and row.scope == "automatic-backup":
                BackupSchedule.objects.filter(installation=self._installation).update(
                    failures=0, last_failure_at=None, next_due_at=self._clock()
                )


def restore_progress(row: OperationalUnit) -> OperationalProgress:
    return OperationalProgress(
        **{field.name: getattr(row, field.name) for field in fields(OperationalProgress)}
    )


def _save(row: OperationalUnit, state: OperationalProgress) -> None:
    for field in fields(OperationalProgress):
        setattr(row, field.name, getattr(state, field.name))
    row.save()


from collections.abc import Callable  # noqa: E402


def _unit_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
