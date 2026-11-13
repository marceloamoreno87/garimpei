from uuid import uuid4

from django.db import models
from django.utils import timezone


class RobotControl(models.Model):
    installation = models.CharField(primary_key=True, max_length=40, default="local")
    requested_enabled = models.BooleanField(default=True)
    revision = models.PositiveBigIntegerField(default=0)
    epoch = models.PositiveBigIntegerField(default=0)
    changed_at = models.DateTimeField(default=timezone.now)
    last_command = models.UUIDField(null=True)


class RobotControlCommand(models.Model):
    id = models.UUIDField(primary_key=True)
    installation = models.ForeignKey(RobotControl, on_delete=models.PROTECT)
    target_enabled = models.BooleanField()
    expected_revision = models.PositiveBigIntegerField()
    result_revision = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)


class RobotOperation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    installation = models.ForeignKey(RobotControl, on_delete=models.PROTECT)
    stage = models.CharField(max_length=40)
    unit_key = models.CharField(max_length=200)
    input_revision = models.CharField(max_length=200)
    resource_generation = models.PositiveBigIntegerField()
    control_epoch = models.PositiveBigIntegerField()
    authorized_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True)
    state = models.CharField(max_length=24, default="active")
    reason = models.CharField(max_length=64, blank=True)
    worker_reference = models.CharField(max_length=80, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["installation", "stage", "unit_key", "resource_generation"],
                name="robot_unit_generation",
            ),
            models.CheckConstraint(
                condition=models.Q(state__in=["active", "completed", "not_started", "unknown"]),
                name="robot_operation_state",
            ),
            models.CheckConstraint(
                condition=~models.Q(state="completed") | models.Q(finished_at__isnull=False),
                name="robot_completed_timestamp",
            ),
        ]
        indexes = [models.Index(fields=["installation", "state"], name="robot_active_lookup")]
