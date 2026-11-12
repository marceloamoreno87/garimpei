"""Additive operational state; business history always retains its original identity."""

from django.db import models


class OperationalUnit(models.Model):
    id = models.UUIDField(primary_key=True)
    installation = models.CharField(max_length=64)
    stage = models.CharField(max_length=20)
    key = models.CharField(max_length=128)
    scope = models.CharField(max_length=512, blank=True)
    revision = models.PositiveBigIntegerField()
    generation = models.PositiveBigIntegerField(default=0)
    pending_since = models.DateTimeField()
    last_progress_at = models.DateTimeField(null=True)
    last_attempt_at = models.DateTimeField(null=True)
    checkpoint = models.CharField(max_length=128, blank=True)
    confirmed_boundaries = models.JSONField(default=list)
    pending = models.PositiveIntegerField(default=1)
    failures = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True)
    reason = models.CharField(max_length=64, default="pending")
    suspended = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["installation", "stage", "key", "revision"], name="operations_unit_revision"
            )
        ]
        indexes = [models.Index(fields=["installation", "stage", "pending_since"])]


class OperationalDiagnostic(models.Model):
    id = models.UUIDField(primary_key=True)
    unit = models.ForeignKey(OperationalUnit, on_delete=models.PROTECT)
    reason = models.CharField(max_length=64)
    created_at = models.DateTimeField()
    protected = models.BooleanField(default=False)


class BackupSchedule(models.Model):
    installation = models.CharField(primary_key=True, max_length=64)
    last_success_at = models.DateTimeField(null=True)
    last_failure_at = models.DateTimeField(null=True)
    next_due_at = models.DateTimeField(null=True)
    failures = models.PositiveIntegerField(default=0)
    revision = models.PositiveBigIntegerField(default=0)


class BackupRecord(models.Model):
    id = models.UUIDField(primary_key=True)
    installation = models.CharField(max_length=64)
    kind = models.CharField(max_length=10)
    source = models.ForeignKey("self", null=True, on_delete=models.PROTECT)
    request_id = models.UUIDField(null=True)
    state = models.CharField(max_length=12, default="creating")
    reason = models.CharField(max_length=64, blank=True)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True)
    snapshot_at = models.DateTimeField(null=True)
    file_key = models.CharField(max_length=100, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True)
    format_version = models.PositiveIntegerField(default=1)
    restoration_state = models.CharField(max_length=12, default="not_tested")
    transferring = models.PositiveIntegerField(default=0)
    scope = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["installation", "request_id"], name="operations_export_request"
            ),
            models.CheckConstraint(
                condition=~models.Q(state="completed")
                | models.Q(
                    finished_at__isnull=False,
                    sha256__regex=r"^[a-f0-9]{64}$",
                    file_key__regex=r"^(completed|exports)/[a-f0-9-]+\.tar\.gz$",
                ),
                name="operations_complete_archive",
            ),
        ]


class RecoveryBarrier(models.Model):
    installation = models.CharField(primary_key=True, max_length=64)
    backup_id = models.UUIDField()
    snapshot_at = models.DateTimeField()
    restored_at = models.DateTimeField()
    state = models.CharField(max_length=12, default="blocked")
    reason = models.CharField(max_length=64, default="unreconciled_interval")
    evidence = models.JSONField(default=dict)
