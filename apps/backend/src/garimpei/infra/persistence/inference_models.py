from uuid import uuid4

from django.db import models


class InferenceControl(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    paused = models.BooleanField(default=False)
    revision = models.PositiveBigIntegerField(default=1)
    generation = models.PositiveBigIntegerField(default=0)
    active_request = models.UUIDField(null=True)
    lease_until = models.DateTimeField(null=True)
    resident = models.BooleanField(default=False)
    service = models.BooleanField(default=False)
    reason = models.CharField(max_length=60, default="service_unavailable")
    checked_at = models.DateTimeField(null=True)
    last_used_at = models.DateTimeField(null=True)
    artifact = models.CharField(max_length=80, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(id=1), name="inference_single_control")
        ]


class InferenceRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    cohort_id = models.UUIDField(null=True)
    cohort_generation = models.PositiveBigIntegerField(null=True)
    observation = models.ForeignKey("ListingObservation", on_delete=models.PROTECT)
    revision = models.PositiveBigIntegerField()
    signature = models.CharField(max_length=64, unique=True)
    artifact = models.CharField(max_length=80)
    prompt_version = models.CharField(max_length=40)
    schema_version = models.CharField(max_length=40)
    state = models.CharField(max_length=30, default="pending", db_index=True)
    reason = models.CharField(max_length=60, blank=True)
    coverage = models.JSONField(default=list)
    created_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    next_attempt_at = models.DateTimeField(null=True)


class InferencePart(models.Model):
    request = models.ForeignKey(InferenceRequest, on_delete=models.PROTECT, related_name="parts")
    position = models.PositiveSmallIntegerField()
    content = models.JSONField()
    state = models.CharField(max_length=20, default="pending")
    attempts = models.PositiveSmallIntegerField(default=0)
    generation = models.PositiveBigIntegerField(default=0)
    result = models.JSONField(null=True)
    metrics = models.JSONField(default=dict)
    reason = models.CharField(max_length=60, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["request", "position"], name="inference_part_position")
        ]
