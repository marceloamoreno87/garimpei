from uuid import uuid4

from django.db import models


class MediaCapture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    observation = models.OneToOneField("ListingObservation", on_delete=models.PROTECT)
    revision = models.PositiveBigIntegerField(default=1)
    presence = models.CharField(max_length=16, default="unknown")
    state = models.CharField(max_length=32, default="pending")
    reason = models.CharField(max_length=64, blank=True)
    complete = models.BooleanField(default=False)
    source_complete = models.BooleanField(default=False)
    known_count = models.PositiveIntegerField(null=True)
    refresh_requested = models.BooleanField(default=False)
    observed_at = models.DateTimeField()
    last_attempt_at = models.DateTimeField(null=True)
    verified_at = models.DateTimeField(null=True)


class MediaAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    listing = models.ForeignKey("Listing", on_delete=models.PROTECT)
    photo_key = models.CharField(max_length=200)
    sha256 = models.CharField(max_length=64)
    mime = models.CharField(max_length=40)
    width = models.PositiveIntegerField()
    height = models.PositiveIntegerField()
    byte_count = models.PositiveBigIntegerField()
    key = models.CharField(max_length=140)
    obtained_at = models.DateTimeField()
    state = models.CharField(max_length=16, default="available")
    thumbnail_state = models.CharField(max_length=16, default="pending")
    thumbnail_hash = models.CharField(max_length=64, blank=True)
    thumbnail_bytes = models.PositiveBigIntegerField(default=0)
    reason = models.CharField(max_length=64, blank=True)
    removed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "photo_key", "sha256"], name="media_asset_content"
            )
        ]


class MediaEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    capture = models.ForeignKey(MediaCapture, on_delete=models.PROTECT, related_name="entries")
    photo_key = models.CharField(max_length=200)
    position = models.PositiveIntegerField()
    primary = models.BooleanField(default=False)
    correlated = models.BooleanField(default=True)
    candidates = models.JSONField(default=list)
    asset = models.ForeignKey(MediaAsset, null=True, on_delete=models.PROTECT)
    generation = models.PositiveBigIntegerField(default=1)
    reason = models.CharField(max_length=64, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["capture", "photo_key"], name="media_capture_photo"),
            models.UniqueConstraint(fields=["capture", "position"], name="media_capture_position"),
            models.UniqueConstraint(
                fields=["capture"], condition=models.Q(primary=True), name="media_capture_primary"
            ),
        ]


class MediaJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    entry = models.ForeignKey(MediaEntry, on_delete=models.PROTECT)
    kind = models.CharField(max_length=16)
    generation = models.PositiveBigIntegerField(default=1)
    state = models.CharField(max_length=16, default="pending")
    attempts = models.PositiveIntegerField(default=0)
    next_at = models.DateTimeField(db_index=True)
    lease_until = models.DateTimeField(null=True)
    lease_generation = models.PositiveBigIntegerField(default=0)
    reserved_bytes = models.PositiveBigIntegerField(default=0)
    reason = models.CharField(max_length=64, blank=True)
    refresh_requested = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entry", "kind", "generation"], name="media_job_generation"
            )
        ]
        indexes = [models.Index(fields=["state", "next_at", "lease_until"])]


class MediaReference(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    asset = models.ForeignKey(MediaAsset, on_delete=models.PROTECT)
    consumer = models.CharField(max_length=80)
    execution = models.CharField(max_length=200)
    created_at = models.DateTimeField()
    released_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["consumer", "execution", "asset"], name="media_reference_execution"
            )
        ]
        indexes = [models.Index(fields=["asset", "released_at"])]
