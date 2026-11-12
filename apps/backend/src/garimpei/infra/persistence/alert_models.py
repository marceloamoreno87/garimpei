from uuid import uuid4

from django.db import models

from garimpei.infra.persistence.listing_models import ListingEvent


class ManualConditionHistory(models.Model):
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    publication_order = models.PositiveBigIntegerField()
    choice = models.CharField(max_length=6)
    revision = models.PositiveBigIntegerField()
    confirmed_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["listing", "revision"], name="manual_history_revision")
        ]


class AlertFeedCursor(models.Model):
    installation = models.CharField(primary_key=True, max_length=40, default="local")
    sequence = models.PositiveBigIntegerField(default=0)
    history_ready = models.BooleanField(default=False)
    dispatch_suspended = models.BooleanField(default=False)
    next_tick = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)


class AlertEventDecision(models.Model):
    assessment_id = models.UUIDField(null=True)
    assessment_revision = models.PositiveBigIntegerField(null=True)
    event = models.OneToOneField(ListingEvent, on_delete=models.PROTECT, to_field="id")
    state = models.CharField(max_length=20, default="waiting")
    reason = models.CharField(max_length=64, default="pending_evaluation")
    condition_revision = models.PositiveBigIntegerField(null=True)
    financial = models.JSONField(default=dict)
    next_action = models.DateTimeField()
    evaluated_at = models.DateTimeField(null=True)

    class Meta:
        indexes = [models.Index(fields=["state", "next_action"])]


class AlertIntent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    decision = models.OneToOneField(AlertEventDecision, null=True, on_delete=models.PROTECT)
    first_decision = models.OneToOneField(
        "FirstEligibilityDecision", null=True, on_delete=models.PROTECT
    )
    session = models.CharField(max_length=200, blank=True)
    recipient = models.CharField(max_length=200, blank=True)
    account = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    financial = models.JSONField(default=dict)
    body_format = models.CharField(max_length=40, blank=True, default="")
    state = models.CharField(max_length=20, default="queued")
    reason = models.CharField(max_length=64, default="pending_channel")
    next_action = models.DateTimeField()
    lease_until = models.DateTimeField(null=True)
    generation = models.PositiveBigIntegerField(default=0)
    failures = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True)
    confirmed_message = models.CharField(max_length=300, null=True)
    confirmed_ack = models.SmallIntegerField(null=True)

    class Meta:
        indexes = [models.Index(fields=["state", "next_action"])]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "recipient", "account", "confirmed_message"],
                name="alert_confirmed_message",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(state="confirmed")
                    | models.Q(
                        confirmed_at__isnull=False,
                        confirmed_message__isnull=False,
                        confirmed_ack__gte=1,
                        confirmed_ack__lte=4,
                    )
                ),
                name="alert_confirmation_evidence",
            ),
        ]


class AlertAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    intent = models.ForeignKey(AlertIntent, on_delete=models.PROTECT, related_name="attempts")
    ordinal = models.PositiveIntegerField()
    generation = models.PositiveBigIntegerField()
    authorized_at = models.DateTimeField()
    state = models.CharField(max_length=20, default="authorized")
    reason = models.CharField(max_length=64, default="transmission_possible")
    message_id = models.CharField(max_length=300, null=True)
    ack = models.SmallIntegerField(null=True)
    finished_at = models.DateTimeField(null=True)
    provenance = models.CharField(max_length=32, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["intent", "ordinal"], name="alert_attempt_order")
        ]


class FirstAlertInventory(models.Model):
    installation = models.CharField(primary_key=True, max_length=40, default="local")
    cursor = models.UUIDField(null=True)
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(null=True)


class FirstAlertIdentity(models.Model):
    installation = models.CharField(max_length=40, default="local")
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    signature = models.CharField(max_length=64, blank=True)
    manual_signature = models.CharField(max_length=64, blank=True)
    generation = models.PositiveBigIntegerField(default=0)
    next_action = models.DateTimeField()
    state = models.CharField(max_length=24, default="waiting")
    reason = models.CharField(max_length=64, default="pending_evaluation")
    intent = models.ForeignKey(
        "AlertIntent", null=True, on_delete=models.PROTECT, related_name="first_identities"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["installation", "listing"], name="first_alert_installation_listing"
            )
        ]
        indexes = [models.Index(fields=["next_action", "listing"])]


class FirstEligibilityDecision(models.Model):
    assessment_id = models.UUIDField(null=True)
    assessment_revision = models.PositiveBigIntegerField(null=True)
    id = models.UUIDField(primary_key=True, default=uuid4)
    identity = models.ForeignKey(
        FirstAlertIdentity, on_delete=models.PROTECT, related_name="decisions"
    )
    generation = models.PositiveBigIntegerField()
    signature = models.CharField(max_length=64)
    cause = models.CharField(max_length=40, default="automatic_input")
    observation = models.ForeignKey("ListingObservation", on_delete=models.PROTECT)
    condition_revision = models.PositiveBigIntegerField(default=0)
    state = models.CharField(max_length=24)
    reason = models.CharField(max_length=64)
    financial = models.JSONField(default=dict)
    reasons = models.JSONField(default=list)
    publication_status = models.CharField(max_length=16)
    published_at = models.DateTimeField(null=True)
    publication_source = models.CharField(max_length=64, blank=True)
    evaluated_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["identity", "generation"], name="first_alert_decision_generation"
            )
        ]
