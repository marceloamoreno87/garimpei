from collections.abc import Callable
from datetime import datetime

from django.db import DatabaseError, transaction
from django.utils import timezone

from garimpei.domain.robot.control import OperationOutcome, RobotCommand, RobotPermit
from garimpei.domain.robot.errors import RobotConflict, RobotUnavailable
from garimpei.infra.persistence.robot_models import (
    RobotControl,
    RobotControlCommand,
    RobotOperation,
)
from garimpei.infra.repository.robot.locking import lock_robot_control


def locked_control() -> RobotControl:
    lock_robot_control()
    try:
        return RobotControl.objects.select_for_update().get(pk="local")
    except RobotControl.DoesNotExist as error:
        # Only the data migration creates this row. Missing state fails closed.
        raise RobotUnavailable() from error


class PostgresRobotRepository:
    def __init__(self, clock: Callable[[], datetime] = timezone.now, worker: str = "") -> None:
        self._clock, self._worker = clock, worker

    def command(self, value: RobotCommand) -> None:
        try:
            with transaction.atomic():
                self._command(value)
        except DatabaseError as error:
            raise RobotUnavailable() from error

    def _command(self, value: RobotCommand) -> None:
        row = locked_control()
        previous = RobotControlCommand.objects.filter(pk=value.id).first()
        if previous is not None:
            if (previous.target_enabled, previous.expected_revision) != (
                value.enabled,
                value.revision,
            ):
                raise RobotConflict()
            return
        if row.revision != value.revision:
            raise RobotConflict()
        if row.requested_enabled != value.enabled:
            row.requested_enabled = value.enabled
            row.revision += 1
            row.epoch += 1
            row.changed_at, row.last_command = self._clock(), value.id
            row.save()
        RobotControlCommand.objects.create(
            id=value.id,
            installation=row,
            target_enabled=value.enabled,
            expected_revision=value.revision,
            result_revision=row.revision,
            created_at=self._clock(),
        )

    def authorize(
        self, stage: str, unit_key: str, input_revision: str, resource_generation: int
    ) -> RobotPermit | None:
        try:
            with transaction.atomic():
                return self._authorize(stage, unit_key, input_revision, resource_generation)
        except DatabaseError as error:
            raise RobotUnavailable() from error

    def _authorize(
        self, stage: str, unit_key: str, input_revision: str, resource_generation: int
    ) -> RobotPermit | None:
        row = locked_control()
        if not row.requested_enabled:
            return None
        if RobotOperation.objects.filter(
            installation=row,
            stage=stage,
            unit_key=unit_key,
            resource_generation=resource_generation,
        ).exists():
            return None
        operation = RobotOperation.objects.create(
            installation=row,
            stage=stage,
            unit_key=unit_key,
            input_revision=input_revision,
            resource_generation=resource_generation,
            control_epoch=row.epoch,
            authorized_at=self._clock(),
            worker_reference=self._worker,
        )
        return RobotPermit(
            operation.id, stage, unit_key, input_revision, resource_generation, row.epoch
        )

    def complete(
        self, permit: RobotPermit, outcome: OperationOutcome = "completed", reason: str = ""
    ) -> None:
        try:
            with transaction.atomic():
                lock_robot_control()
                RobotOperation.objects.filter(
                    pk=permit.id,
                    stage=permit.stage,
                    unit_key=permit.unit_key,
                    input_revision=permit.input_revision,
                    resource_generation=permit.resource_generation,
                    control_epoch=permit.epoch,
                    state__in=["active", "unknown"],
                ).update(state=outcome, reason=reason, finished_at=self._clock())
        except DatabaseError as error:
            raise RobotUnavailable() from error
