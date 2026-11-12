from uuid import uuid4

from django.db import models


class ValuationProgress(models.Model):
    listing = models.OneToOneField("Listing", primary_key=True, on_delete=models.PROTECT)
    requested = models.PositiveBigIntegerField(default=0)
    signature = models.CharField(max_length=64, blank=True)
    current = models.ForeignKey("ValuationEvaluation", null=True, on_delete=models.PROTECT)
    due_at = models.DateTimeField(null=True, db_index=True)


class ValuationWork(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    revision = models.PositiveBigIntegerField()
    snapshot = models.JSONField()
    requested_at = models.DateTimeField()
    next_attempt_at = models.DateTimeField(db_index=True)
    lease_until = models.DateTimeField(null=True)
    completed = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    diagnostic = models.CharField(max_length=80, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["listing", "revision"], name="valuation_work_revision")
        ]


class ValuationEvaluation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    work = models.OneToOneField(ValuationWork, on_delete=models.PROTECT)
    result = models.JSONField()
