from uuid import uuid4

from django.db import models


class ExplorationRevision(models.Model):
    id = models.UUIDField(default=uuid4, unique=True)
    sequence = models.BigAutoField(primary_key=True)
    published_at = models.DateTimeField()
    superseded_at = models.DateTimeField(null=True)
    signature = models.CharField(max_length=64)


class ExplorationOffer(models.Model):
    revision = models.ForeignKey(ExplorationRevision, on_delete=models.CASCADE)
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    first_seen_at = models.DateTimeField()
    search = models.TextField()
    categories = models.JSONField(default=list)
    automatic_tab = models.CharField(max_length=10)
    pickup = models.BooleanField()
    shipping = models.BooleanField()
    visible = models.BooleanField()
    profit = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    payload = models.JSONField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["revision", "listing"], name="exploration_revision_listing"
            )
        ]
        indexes = [
            models.Index(
                fields=[
                    "revision",
                    "visible",
                    "automatic_tab",
                    "-profit",
                    "-first_seen_at",
                    "listing",
                ]
            )
        ]
