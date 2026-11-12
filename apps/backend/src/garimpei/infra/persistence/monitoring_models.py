import uuid

from django.db import models


class MonitoringConfiguration(models.Model):
    id = models.UUIDField(primary_key=True)
    slot = models.CharField(max_length=8, unique=True)
    revision = models.PositiveBigIntegerField(default=0)
    source = models.CharField(max_length=32, default="facebook_marketplace")
    cep = models.CharField(max_length=8, null=True)
    shipping_estimate = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    resale_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    completed_at = models.DateTimeField(null=True)
    completion_revision = models.PositiveBigIntegerField(null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "persistence_monitoringconfiguration"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(slot__in=["draft", "active"]), name="monitoring_slot"
            ),
            models.CheckConstraint(
                condition=models.Q(shipping_estimate__isnull=True)
                | models.Q(shipping_estimate__gte=0, shipping_estimate__lte=999999.99),
                name="monitoring_shipping_range",
            ),
            models.CheckConstraint(
                condition=models.Q(resale_fee_percent__isnull=True)
                | models.Q(resale_fee_percent__gte=0, resale_fee_percent__lte=100),
                name="monitoring_fee_range",
            ),
            models.CheckConstraint(
                condition=models.Q(slot="draft", completed_at__isnull=True)
                | models.Q(
                    slot="active",
                    completed_at__isnull=False,
                    cep__isnull=False,
                    resale_fee_percent__isnull=False,
                ),
                name="monitoring_completion",
            ),
        ]


class MonitoringInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    configuration = models.ForeignKey(MonitoringConfiguration, on_delete=models.CASCADE)
    kind = models.CharField(max_length=8)
    key = models.CharField(max_length=512)
    label = models.CharField(max_length=255)

    class Meta:
        db_table = "persistence_monitoringinterest"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=["category", "product"]),
                name="monitoring_interest_kind",
            ),
            models.UniqueConstraint(
                fields=["configuration", "kind", "key"], name="monitoring_interest_unique"
            ),
        ]
