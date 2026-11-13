"""Append-only gold decisions and the installation-wide policy adoption fence."""

from uuid import uuid4

from django.db import models


class GoldQualification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    observation = models.ForeignKey("ListingObservation", on_delete=models.PROTECT)
    purpose_key = models.CharField(max_length=48)
    policy = models.CharField(max_length=40)
    input_fingerprint = models.CharField(max_length=64)
    state = models.CharField(max_length=16)
    reason = models.CharField(max_length=64)
    reasons = models.JSONField(default=list)
    evidence = models.JSONField()
    evaluated_at = models.DateTimeField()
    valid_until = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "purpose_key", "policy", "input_fingerprint"],
                name="gold_decision_input_once",
            ),
            models.CheckConstraint(
                condition=models.Q(state__in=["qualified", "waiting", "blocked"]),
                name="gold_decision_state",
            ),
        ]
        indexes = [
            models.Index(
                fields=["listing", "purpose_key", "evaluated_at"], name="gold_current_lookup"
            ),
            models.Index(fields=["state", "valid_until"], name="gold_validity_lookup"),
        ]


class GoldPolicyAdoption(models.Model):
    installation = models.CharField(primary_key=True, max_length=40, default="local")
    policy = models.CharField(max_length=40, default="gold-alert-v1")
    state = models.CharField(max_length=16, default="pending")
    activated_at = models.DateTimeField(null=True)
    consumer_version = models.CharField(max_length=40, default="gold-alert-v1")
    inventory = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(state__in=["pending", "active"]), name="gold_adoption_state"
            ),
        ]
