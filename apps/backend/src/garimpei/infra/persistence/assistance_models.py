from uuid import uuid4

from django.db import models
from django.utils.timezone import now


class AssistanceOperationsSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    revision = models.PositiveBigIntegerField(unique=True)
    content_hash = models.CharField(max_length=64, unique=True)
    facts = models.JSONField()
    whitelist_version = models.CharField(max_length=32, default="operations-facts-v1")
    created_at = models.DateTimeField(default=now)


class AssistanceReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    purpose = models.CharField(max_length=32)
    target_kind = models.CharField(max_length=32)
    target_id = models.UUIDField()
    observation = models.ForeignKey(
        "ListingObservation", null=True, on_delete=models.PROTECT, related_name="assistance_reviews"
    )
    candidate_observation = models.ForeignKey(
        "ListingObservation", null=True, on_delete=models.PROTECT, related_name="candidate_reviews"
    )
    operations_snapshot = models.ForeignKey(
        AssistanceOperationsSnapshot, null=True, on_delete=models.PROTECT
    )
    input_signature = models.CharField(max_length=64)
    generation = models.PositiveBigIntegerField()
    input_snapshot = models.JSONField()
    state = models.CharField(max_length=32, default="pending")
    reason_code = models.CharField(max_length=64, default="waiting_analysis")
    result = models.JSONField(null=True)
    consumed_by = models.JSONField(default=list)
    cache_reuses = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(default=now)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["purpose", "target_kind", "target_id", "input_signature"],
                name="assistance_review_signature",
            )
        ]
        indexes = [
            models.Index(
                fields=["target_kind", "target_id", "purpose", "created_at"],
                name="assistance_target_purpose",
            ),
            models.Index(fields=["state", "updated_at"], name="assistance_pending"),
        ]


class AssistanceReviewRequest(models.Model):
    review = models.ForeignKey(AssistanceReview, on_delete=models.PROTECT, related_name="requests")
    request = models.ForeignKey("InferenceRequest", on_delete=models.PROTECT)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["review", "request"], name="assistance_request_once")
        ]


class AssistanceCommand(models.Model):
    id = models.UUIDField(primary_key=True)
    command_hash = models.CharField(max_length=64)
    review = models.ForeignKey(AssistanceReview, on_delete=models.PROTECT)


class AssistancePolicy(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1)
    active = models.BooleanField(default=False)
    version = models.CharField(max_length=64, default="assisted-evidence-v1")
    adopted_at = models.DateTimeField(null=True)
