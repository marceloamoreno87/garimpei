from uuid import uuid4

from django.db import models


class ComparableInvestigation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    signature = models.CharField(max_length=64, unique=True)
    product_key = models.CharField(max_length=240)
    configuration_id = models.UUIDField()
    configuration_revision = models.PositiveBigIntegerField()
    origin_interest = models.CharField(max_length=450)
    scope_key = models.CharField(max_length=64)
    context = models.JSONField()
    limits = models.JSONField()
    term = models.CharField(max_length=400)
    policy = models.CharField(max_length=64)
    state = models.CharField(max_length=24, default="pending")
    reason = models.CharField(max_length=80, default="research_requested")
    pages = models.PositiveIntegerField(default=0)
    details = models.PositiveIntegerField(default=0)
    attempts = models.PositiveIntegerField(default=0)
    failures = models.PositiveIntegerField(default=0)
    last_turn = models.PositiveBigIntegerField(default=0)
    generation = models.PositiveBigIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True)
    lease_until = models.DateTimeField(null=True)
    last_progress_at = models.DateTimeField(null=True)
    requested_at = models.DateTimeField()
    cursor = models.CharField(max_length=4103, null=True)
    signatures = models.JSONField(default=list)
    buffer = models.JSONField(default=list)
    cycle = models.ForeignKey("CollectionCycle", null=True, on_delete=models.PROTECT)

    class Meta:
        indexes = [models.Index(fields=["state", "next_attempt_at"], name="research_next_action")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    state__in=[
                        "pending",
                        "running",
                        "waiting_evidence",
                        "waiting_retry",
                        "suspended_access",
                        "limited",
                        "sufficient",
                        "exhausted",
                        "superseded",
                    ]
                ),
                name="research_state_valid",
            )
        ]


class InvestigationTarget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    investigation = models.ForeignKey(
        ComparableInvestigation, on_delete=models.PROTECT, related_name="targets"
    )
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    observation = models.ForeignKey("ListingObservation", on_delete=models.PROTECT)
    manual_revision = models.PositiveBigIntegerField(default=0)
    configuration_revision = models.PositiveBigIntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["investigation", "listing", "observation", "manual_revision"],
                name="research_target_revision_once",
            )
        ]


class ResearchQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    investigation = models.ForeignKey(
        ComparableInvestigation, on_delete=models.PROTECT, related_name="queries"
    )
    ordinal = models.PositiveIntegerField()
    term = models.CharField(max_length=400)
    requested = models.JSONField()
    observed = models.JSONField()
    state = models.CharField(max_length=24)
    reason = models.CharField(max_length=80, blank=True)
    requested_at = models.DateTimeField()
    confirmed_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["investigation", "ordinal"], name="research_query_once")
        ]


class ResearchCandidateDecision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    query = models.ForeignKey(ResearchQuery, on_delete=models.PROTECT, related_name="decisions")
    target = models.ForeignKey(InvestigationTarget, on_delete=models.PROTECT)
    observation = models.ForeignKey("ListingObservation", on_delete=models.PROTECT)
    policy = models.CharField(max_length=64)
    decision = models.CharField(max_length=40)
    reasons = models.JSONField(default=list)
    evidence = models.JSONField()
    recorded_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["query", "target", "observation", "policy"],
                name="research_candidate_decision_once",
            )
        ]
