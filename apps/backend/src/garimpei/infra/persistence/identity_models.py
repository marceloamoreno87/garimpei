from uuid import uuid4

from django.db import models


class ManualIdentityRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    revision = models.PositiveBigIntegerField()
    observation = models.ForeignKey("ListingObservation", on_delete=models.PROTECT)
    action = models.CharField(max_length=16)
    resolution = models.CharField(max_length=24, blank=True)
    values = models.JSONField(default=dict)
    reviewed_conflicts = models.JSONField(default=list)
    recorded_at = models.DateTimeField()
    previous = models.ForeignKey("self", null=True, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "revision"], name="identity_manual_revision_once"
            )
        ]


class ProductIdentification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    observation = models.ForeignKey("ListingObservation", on_delete=models.PROTECT)
    manual_revision = models.PositiveBigIntegerField(default=0)
    policy = models.CharField(max_length=40)
    state = models.CharField(max_length=32)
    product_key = models.CharField(max_length=240, null=True)
    result = models.JSONField()
    recorded_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["observation", "manual_revision", "policy"],
                name="identity_observation_revision_once",
            )
        ]
        indexes = [models.Index(fields=["listing", "recorded_at"], name="identity_history_listing")]


class IdentityProgress(models.Model):
    listing = models.OneToOneField(
        "Listing", primary_key=True, on_delete=models.PROTECT, related_name="identity_progress"
    )
    manual_revision = models.PositiveBigIntegerField(default=0)
    manual = models.ForeignKey(ManualIdentityRevision, null=True, on_delete=models.PROTECT)
    current = models.ForeignKey(ProductIdentification, null=True, on_delete=models.PROTECT)
