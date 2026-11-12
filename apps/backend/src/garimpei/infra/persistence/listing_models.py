from uuid import uuid4

from django.db import models

from garimpei.domain.listing.listing import MAX_INTEREST_KEY_LENGTH


class CollectionState(models.Model):
    configuration_id = models.UUIDField()
    source = models.CharField(max_length=40)
    current = models.ForeignKey("CollectionCycle", null=True, on_delete=models.PROTECT)
    monitoring_started_at = models.DateTimeField(null=True)
    initial_completed_at = models.DateTimeField(null=True)
    initial_scope = models.CharField(max_length=64, blank=True)
    last_success_at = models.DateTimeField(null=True)
    next_attempt_at = models.DateTimeField(null=True, db_index=True)
    source_not_before = models.DateTimeField(null=True)
    lease_until = models.DateTimeField(null=True)
    generation = models.PositiveBigIntegerField(default=0)
    failures = models.PositiveIntegerField(default=0)
    access_suspended = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["configuration_id", "source"], name="collection_configuration_source"
            )
        ]


class CollectionCycle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    state = models.ForeignKey(CollectionState, on_delete=models.PROTECT, related_name="cycles")
    scope_key = models.CharField(max_length=64)
    revision = models.PositiveBigIntegerField()
    phase = models.CharField(max_length=16, default="scheduled")
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)
    scanned = models.BooleanField(default=False)
    window_start = models.DateTimeField(null=True)
    window_end = models.DateTimeField(null=True)
    window_evidence = models.JSONField(default=dict)
    origin = models.JSONField(null=True)
    planned = models.JSONField(default=list)
    results = models.JSONField(default=dict)
    diagnostics = models.JSONField(default=dict)
    published_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["state", "started_at"])]


class CollectionCandidate(models.Model):
    cycle = models.ForeignKey(CollectionCycle, on_delete=models.CASCADE)
    query_key = models.CharField(max_length=450)
    external_id = models.CharField(max_length=40)
    candidates = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cycle", "query_key", "external_id"], name="collection_candidate_unit_id"
            )
        ]
        indexes = [models.Index(fields=["cycle", "external_id"])]


class Listing(models.Model):
    media_tracking_active = models.BooleanField(default=True)
    media_refresh_after = models.DateTimeField(null=True)
    id = models.UUIDField(primary_key=True, default=uuid4)
    source = models.CharField(max_length=40)
    external_id = models.CharField(max_length=40)
    canonical_url = models.URLField()
    first_seen_at = models.DateTimeField()
    origin = models.CharField(max_length=16)
    ordinal = models.PositiveBigIntegerField(default=0)
    publication_order = models.PositiveBigIntegerField(default=0)
    discovery_emitted = models.BooleanField(default=False)
    latest = models.ForeignKey(
        "ListingObservation", null=True, on_delete=models.PROTECT, related_name="+"
    )
    known_price = models.ForeignKey(
        "ListingObservation", null=True, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "external_id"], name="listing_source_id")
        ]


class ListingObservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="observations")
    cycle = models.ForeignKey(CollectionCycle, on_delete=models.PROTECT)
    ordinal = models.PositiveBigIntegerField()
    observed_at = models.DateTimeField()
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    freight = models.DecimalField(max_digits=14, decimal_places=2, null=True)
    evidence = models.JSONField()
    coverage = models.JSONField()
    provenance = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "ordinal"], name="listing_observation_order"
            ),
            models.UniqueConstraint(fields=["cycle", "listing"], name="listing_observation_cycle"),
            models.CheckConstraint(
                condition=models.Q(price__gte=0) | models.Q(price__isnull=True),
                name="listing_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(freight__gte=0) | models.Q(freight__isnull=True),
                name="listing_freight_nonnegative",
            ),
        ]


class ListingInterestMatch(models.Model):
    observation = models.ForeignKey(
        ListingObservation, on_delete=models.PROTECT, related_name="matches"
    )
    kind = models.CharField(max_length=12)
    key = models.CharField(max_length=MAX_INTEREST_KEY_LENGTH)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["observation", "kind", "key"], name="listing_observation_interest"
            )
        ]
        indexes = [models.Index(fields=["kind", "key"])]


class ListingEvent(models.Model):
    publication_order = models.PositiveBigIntegerField(null=True)
    sequence = models.BigAutoField(primary_key=True)
    id = models.UUIDField(default=uuid4, unique=True)
    kind = models.CharField(max_length=16)
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT)
    observation = models.ForeignKey(ListingObservation, on_delete=models.PROTECT)
    previous = models.ForeignKey(
        ListingObservation, null=True, on_delete=models.PROTECT, related_name="+"
    )
    silent = models.BooleanField()
    occurred_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "observation", "kind"], name="listing_observation_event"
            )
        ]


class ManualCondition(models.Model):
    listing = models.OneToOneField(
        Listing, primary_key=True, on_delete=models.PROTECT, related_name="manual_condition"
    )
    choice = models.CharField(max_length=6)
    revision = models.PositiveBigIntegerField()
    updated_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(choice__in=["good", "defect"]), name="condition_choice_valid"
            ),
            models.CheckConstraint(
                condition=models.Q(revision__gte=1), name="condition_revision_positive"
            ),
        ]
