from uuid import uuid4

from django.db import models


class NavigationWork(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    cycle = models.ForeignKey("CollectionCycle", on_delete=models.PROTECT)
    configuration_id = models.UUIDField()
    source = models.CharField(max_length=40)
    scope_key = models.CharField(max_length=64)
    revision = models.PositiveBigIntegerField()
    origin_interest = models.CharField(max_length=450)
    original_term = models.CharField(max_length=400)
    purpose = models.CharField(max_length=16, default="active")
    front = models.CharField(max_length=16)
    phase = models.CharField(max_length=24, default="pending")
    reason = models.CharField(max_length=80, blank=True)
    generation = models.PositiveBigIntegerField(default=0)
    last_turn = models.PositiveBigIntegerField(default=0)
    failures = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True)
    last_progress_at = models.DateTimeField(null=True)
    request_id = models.UUIDField(null=True, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cycle", "origin_interest", "front", "purpose", "original_term"],
                name="navigation_work_context",
            ),
            models.CheckConstraint(
                condition=models.Q(front__in=["discovery", "investigation"]),
                name="navigation_front_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(purpose__in=["active", "research"]),
                name="navigation_purpose_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    phase__in=[
                        "pending",
                        "running",
                        "waiting",
                        "partial",
                        "suspended",
                        "complete",
                        "superseded",
                    ]
                ),
                name="navigation_phase_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["phase", "next_attempt_at"], name="navigation_due"),
            models.Index(fields=["configuration_id", "revision"], name="navigation_configuration"),
        ]


class NavigationCheckpoint(models.Model):
    work = models.OneToOneField(NavigationWork, primary_key=True, on_delete=models.PROTECT)
    catalog_version = models.CharField(max_length=40)
    limits = models.JSONField(default=dict)
    context = models.JSONField(default=dict)
    context_hash = models.CharField(max_length=64)
    terms = models.JSONField(default=list)
    term_index = models.PositiveIntegerField(default=0)
    cursor = models.CharField(max_length=4103, null=True)
    signatures = models.JSONField(default=list)
    buffered_candidates = models.JSONField(default=list)
    buffer_proof = models.CharField(max_length=80, null=True)
    invalid_cards = models.PositiveIntegerField(default=0)
    pages = models.PositiveIntegerField(default=0)
    details = models.PositiveIntegerField(default=0)
    pending_unit = models.CharField(max_length=450, blank=True)
    generation = models.PositiveBigIntegerField(default=0)


class NavigationUnitReceipt(models.Model):
    work = models.ForeignKey(NavigationWork, on_delete=models.PROTECT)
    unit_key = models.CharField(max_length=450)
    input_revision = models.PositiveBigIntegerField()
    generation = models.PositiveBigIntegerField()
    confirmed_at = models.DateTimeField()
    turn_order = models.PositiveBigIntegerField()
    consumed_pages = models.PositiveIntegerField(default=0)
    consumed_details = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=80)
    observation_ids = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["work", "unit_key", "input_revision"], name="navigation_unit_once"
            )
        ]


class NicheSuggestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    configuration_id = models.UUIDField()
    revision = models.PositiveBigIntegerField()
    origin_interest = models.CharField(max_length=450)
    original_term = models.CharField(max_length=400)
    term = models.CharField(max_length=400)
    relation_key = models.CharField(max_length=80)
    catalog_version = models.CharField(max_length=40)
    relation_reason = models.CharField(max_length=500)
    state = models.CharField(max_length=20, default="inconclusive")
    reason = models.CharField(max_length=80, default="evidence_pending")
    observed_at = models.DateTimeField(null=True)
    last_slice_at = models.DateTimeField(null=True)
    pages = models.PositiveIntegerField(default=0)
    details = models.PositiveIntegerField(default=0)
    pending_id = models.CharField(max_length=40, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["configuration_id", "origin_interest", "term", "relation_key"],
                name="navigation_suggestion_origin",
            ),
            models.CheckConstraint(
                condition=models.Q(state__in=["inconclusive", "supported", "limited"]),
                name="navigation_suggestion_state",
            ),
        ]
        indexes = [models.Index(fields=["state", "observed_at"], name="navigation_suggestion_date")]


class SuggestionEvidence(models.Model):
    suggestion = models.ForeignKey(
        NicheSuggestion, on_delete=models.PROTECT, related_name="evidence"
    )
    source = models.CharField(max_length=40)
    external_id = models.CharField(max_length=40)
    canonical_url = models.URLField()
    excerpt = models.CharField(max_length=500)
    observed_at = models.DateTimeField()
    context_hash = models.CharField(max_length=64)
    catalog_version = models.CharField(max_length=40)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["suggestion", "source", "external_id", "catalog_version"],
                name="navigation_suggestion_evidence",
            )
        ]
