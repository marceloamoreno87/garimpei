from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from django.db import connection, transaction
from django.db.models import Exists, F, Max, OuterRef, Q, Sum

from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.media import (
    AnalysisMedia,
    Manifest,
    MediaClaim,
    MediaFile,
    Transfer,
    Variant,
)
from garimpei.domain.media.policy import MediaPolicy
from garimpei.infra.persistence.listing_models import CollectionState, Listing, ListingObservation
from garimpei.infra.persistence.media_models import (
    MediaAsset,
    MediaCapture,
    MediaEntry,
    MediaJob,
    MediaReference,
)
from garimpei.infra.repository.media.captures import create_capture
from garimpei.infra.repository.media.mapper import photo_view


@contextmanager
def quota_lock() -> Iterator[None]:
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [140014])
        yield


class PostgresMediaRepository:
    def __init__(self, policy: MediaPolicy, physical_bytes: Callable[[], int]) -> None:
        self._policy, self._physical_bytes = policy, physical_bytes

    def claim(self, identity: UUID, now: datetime) -> MediaClaim | None:
        with quota_lock():
            job = (
                MediaJob.objects.select_for_update(of=("self",))
                .select_related("entry__capture__observation", "entry__asset")
                .filter(id=identity)
                .first()
            )
            if job is None or job.state in {"done", "failed"} or job.next_at > now:
                return None
            if job.lease_until and job.lease_until > now:
                return None
            entry = job.entry
            if not self._policy.budget_bytes:
                self._capture_state(
                    entry, "configuration_required", "media_configuration_required", now
                )
                return None
            if (
                MediaJob.objects.filter(state="running", lease_until__gt=now)
                .exclude(id=job.id)
                .exists()
            ):
                return None
            # Expired reservations have no owner; stale publishers fail the generation check.
            MediaJob.objects.filter(lease_until__lte=now).update(reserved_bytes=0)
            files = (
                MediaAsset.objects.exclude(state="removed")
                .values("key")
                .annotate(n=Max("byte_count"), t=Max("thumbnail_bytes"))
            )
            physical = self._storage_size(entry, now)
            if physical is None:
                return None
            used = max(sum(r["n"] + r["t"] for r in files), physical)
            reserved = MediaJob.objects.aggregate(n=Sum("reserved_bytes"))["n"] or 0
            required = self._policy.max_file_bytes * (2 if job.kind == "download" else 1)
            if used + reserved + required > self._policy.budget_bytes:
                self._capture_state(entry, "partial", "media_storage_budget", now)
                return None
            job.lease_generation += 1
            job.state, job.lease_until = (
                "running",
                now + timedelta(seconds=self._policy.lease_seconds),
            )
            job.reserved_bytes, job.attempts = required, job.attempts + 1
            job.save()
            self._capture_state(entry, "running", entry.capture.reason, now)
            return MediaClaim(
                job.id,
                job.lease_generation,
                job.kind,
                entry.capture.observation.listing_id,
                entry.capture.observation_id,
                entry.id,
                entry.photo_key,
                tuple(Variant(**row) for row in entry.candidates),
                job.attempts,
                entry.asset_id,
            )

    def _storage_size(self, entry: MediaEntry, now: datetime) -> int | None:
        try:
            return self._physical_bytes()
        except MediaError as failure:
            self._capture_state(entry, "configuration_required", failure.code, now)
            return None

    def _owned(self, claim: MediaClaim, now: datetime) -> MediaJob:
        job = (
            MediaJob.objects.select_for_update(of=("self",))
            .select_related("entry__capture")
            .get(id=claim.id)
        )
        if (
            job.entry_id != claim.entry_id
            or job.lease_generation != claim.generation
            or job.state != "running"
            or not job.lease_until
            or job.lease_until <= now
        ):
            raise MediaError("media_stale_generation", 409)
        return job

    def publish(
        self, claim: MediaClaim, content: Transfer, key: str, now: datetime, reason: str = ""
    ) -> None:
        with quota_lock():
            job = self._owned(claim, now)
            entry = job.entry
            asset, limitation = self._best_asset(entry, claim, content, key, now)
            entry.asset = asset
            reason = reason or limitation
            entry.reason = reason
            entry.save(update_fields=["asset", "reason"])
            job.state, job.reserved_bytes, job.lease_until = "done", 0, None
            job.save()
            if asset.thumbnail_state != "ready":
                MediaJob.objects.get_or_create(
                    entry=entry,
                    kind="thumbnail",
                    generation=entry.generation,
                    defaults={"id": uuid4(), "next_at": now},
                )
            self._settle(entry.capture, now)

    @staticmethod
    def _best_asset(
        entry: MediaEntry, claim: MediaClaim, content: Transfer, key: str, now: datetime
    ) -> tuple[MediaAsset, str]:
        prior = entry.asset
        if prior and prior.width * prior.height > content.width * content.height:
            return prior, "media_lower_quality_preserved"
        asset, _ = MediaAsset.objects.get_or_create(
            listing_id=claim.listing_id,
            photo_key=claim.photo_key,
            sha256=content.sha256,
            defaults={
                "id": uuid4(),
                "mime": content.mime,
                "width": content.width,
                "height": content.height,
                "byte_count": len(content.data),
                "key": key,
                "obtained_at": now,
            },
        )
        if asset.state != "available":
            raise MediaError("media_content_removed", 409)
        return asset, ""

    def fail(self, claim: MediaClaim, code: str, now: datetime, retry_after: int = 0) -> None:
        with quota_lock():
            job = self._owned(claim, now)
            permanent = code in {
                "media_content_rejected",
                "media_pixel_limit",
                "media_file_limit",
                "media_destination_rejected",
                "media_peer_rejected",
            }
            delay = None if permanent else self._policy.retry_delay(job.attempts, retry_after)
            job.state = "failed" if delay is None else "pending"
            job.next_at = now + timedelta(seconds=delay or 0)
            job.lease_until, job.reserved_bytes, job.reason = None, 0, code
            if code == "media_source_expired" and not job.refresh_requested:
                job.refresh_requested = True
                self._refresh(job.entry.capture, now)
            job.save()
            job.entry.reason = code
            job.entry.save(update_fields=["reason"])
            if claim.kind == "thumbnail" and claim.asset_id:
                MediaAsset.objects.filter(id=claim.asset_id).update(thumbnail_state="failed")
            self._settle(job.entry.capture, now)

    def thumbnail(self, claim: MediaClaim, file: MediaFile, now: datetime) -> None:
        with quota_lock():
            job = self._owned(claim, now)
            assert claim.asset_id is not None
            MediaAsset.objects.filter(id=claim.asset_id, state="available").update(
                thumbnail_state="ready", thumbnail_hash=file.sha256, thumbnail_bytes=file.byte_count
            )
            job.state, job.reserved_bytes, job.lease_until = "done", 0, None
            job.save()
            MediaEntry.objects.filter(id=claim.entry_id, reason="media_thumbnail_failed").update(
                reason=""
            )
            self._settle(job.entry.capture, now)

    def original(self, claim: MediaClaim) -> MediaFile:
        if claim.asset_id is None:
            raise MediaError("MEDIA_FILE_UNAVAILABLE")
        asset = MediaAsset.objects.get(id=claim.asset_id, state="available")
        return MediaFile(asset.id, asset.key, asset.mime, asset.sha256, asset.byte_count)

    def due(self, now: datetime) -> tuple[UUID, ...]:
        if not self._policy.budget_bytes:
            return ()
        return tuple(
            MediaJob.objects.filter(
                Q(state="pending") | Q(state="running", lease_until__lte=now), next_at__lte=now
            )
            .order_by("next_at")
            .values_list("id", flat=True)[:20]
        )

    @staticmethod
    def _capture_state(entry: MediaEntry, state: str, reason: str, now: datetime) -> None:
        MediaCapture.objects.filter(id=entry.capture_id).update(
            state=state, reason=reason, last_attempt_at=now
        )

    def _settle(self, capture: MediaCapture, now: datetime) -> None:
        entries = list(MediaEntry.objects.filter(capture=capture).select_related("asset"))
        failures = [entry.reason for entry in entries if entry.reason]
        complete = (
            capture.source_complete and not failures and all(entry.asset_id for entry in entries)
        )
        capture.complete = complete
        capture.state = (
            "ready" if complete else "partial" if any(e.asset_id for e in entries) else "failed"
        )
        capture.reason = "" if complete else failures[0] if failures else capture.reason
        capture.revision += 1
        capture.last_attempt_at = now
        if complete:
            capture.verified_at = now
        capture.save()

    def acquire(
        self,
        listing: UUID,
        observation: UUID,
        version: UUID,
        consumer: str,
        execution: str,
        now: datetime,
    ) -> AnalysisMedia:
        if not consumer or len(consumer) > 80 or not execution or len(execution) > 200:
            raise MediaError("MEDIA_REFERENCE_INVALID", 400)
        with quota_lock():
            asset = (
                MediaAsset.objects.select_for_update(of=("self",))
                .filter(id=version, listing_id=listing)
                .first()
            )
            entry = (
                MediaEntry.objects.select_related("asset")
                .filter(
                    asset_id=version,
                    capture__observation_id=observation,
                    capture__observation__listing_id=listing,
                )
                .first()
            )
            if asset is None or entry is None:
                raise MediaError("MEDIA_NOT_FOUND", 404)
            if asset.state != "available":
                raise MediaError("MEDIA_REMOVED", 409)
            reference, created = MediaReference.objects.get_or_create(
                asset=asset,
                consumer=consumer,
                execution=execution,
                defaults={"id": uuid4(), "created_at": now},
            )
            if not created and reference.released_at is not None:
                raise MediaError("MEDIA_REFERENCE_RELEASED", 409)
            return AnalysisMedia(reference.id, listing, observation, photo_view(entry))

    def release(self, identity: UUID, now: datetime) -> None:
        with quota_lock():
            MediaReference.objects.filter(id=identity, released_at=None).update(released_at=now)

    def cleanable(self, now: datetime) -> tuple[MediaFile, ...]:
        with quota_lock():
            rows = (
                MediaAsset.objects.select_for_update(of=("self",))
                .filter(listing__media_tracking_active=False)
                .exclude(state="removed")
                .order_by("obtained_at")[:100]
            )
            return tuple(file for asset in rows if (file := self._mark_removing(asset)) is not None)

    @staticmethod
    def _mark_removing(asset: MediaAsset) -> MediaFile | None:
        if MediaReference.objects.filter(asset=asset, released_at=None).exists():
            return None
        asset.state, asset.reason = "removing", "media_retention_ended"
        asset.save(update_fields=["state", "reason"])
        return MediaFile(asset.id, asset.key, asset.mime, asset.sha256, asset.byte_count)

    def removed(self, identity: UUID, now: datetime) -> None:
        with quota_lock():
            MediaAsset.objects.filter(id=identity, state="removing").update(
                state="removed", thumbnail_state="removed", removed_at=now
            )

    def retry(self, listing: UUID, capture: UUID, revision: int, now: datetime) -> None:
        if not self._policy.budget_bytes:
            raise MediaError("MEDIA_CONFIGURATION_REQUIRED", 409)
        with quota_lock():
            record = (
                MediaCapture.objects.select_for_update(of=("self",))
                .select_related("observation__listing")
                .filter(id=capture, observation__listing_id=listing)
                .first()
            )
            if record is None:
                raise MediaError("MEDIA_NOT_FOUND", 404)
            if (
                record.revision != revision
                or record.observation.listing.latest_id != record.observation_id
            ):
                raise MediaError("MEDIA_REVISION_CONFLICT", 409)
            for entry in record.entries.all():
                self._retry_entry(entry, now)

    @staticmethod
    def _retry_entry(entry: MediaEntry, now: datetime) -> None:
        pending = MediaJob.objects.filter(entry=entry).exclude(state__in=["failed", "done"])
        if pending.exists():
            return
        entry.generation += 1
        entry.save(update_fields=["generation"])
        kind = (
            "thumbnail"
            if entry.asset_id and entry.asset and entry.asset.thumbnail_state != "ready"
            else "download"
        )
        previous = MediaJob.objects.filter(entry=entry, kind=kind).order_by("-next_at").first()
        MediaJob.objects.create(
            id=uuid4(),
            entry=entry,
            kind=kind,
            generation=entry.generation,
            next_at=max(now, previous.next_at) if previous else now,
        )

    def backfill(self, now: datetime) -> None:
        if not self._policy.budget_bytes:
            return
        with quota_lock():
            missing = ListingObservation.objects.filter(
                listing__latest_id=F("id"), mediacapture__isnull=True
            ).order_by("observed_at")[:5]
            for observation in missing:
                create_capture(observation, Manifest(), self._policy, now)
        with quota_lock():
            for capture in MediaCapture.objects.filter(
                presence="unknown", refresh_requested=False
            ).select_related("observation__cycle")[:5]:
                self._refresh(capture, now)

    @staticmethod
    def _refresh(capture: MediaCapture, now: datetime) -> None:
        # Existing collection owns the one browser profile. Limit refresh across observations.
        listing = Listing.objects.select_for_update(of=("self",)).get(
            id=capture.observation.listing_id
        )
        if listing.media_refresh_after and listing.media_refresh_after > now:
            return
        changed = CollectionState.objects.filter(
            id=capture.observation.cycle.state_id, access_suspended=False, lease_until__isnull=True
        ).update(next_attempt_at=now)
        if not changed:
            return
        listing.media_refresh_after = now + timedelta(seconds=300)
        listing.save(update_fields=["media_refresh_after"])
        MediaCapture.objects.filter(id=capture.id).update(refresh_requested=True)

    def protected_versions(self, execution: str, now: datetime) -> tuple[AnalysisMedia, ...]:
        """Acquire backup pins atomically before the caller reads or exports immutable bytes."""
        with quota_lock():
            active = MediaReference.objects.filter(asset_id=OuterRef("pk"), released_at=None)
            assets = (
                MediaAsset.objects.select_for_update(of=("self",))
                .annotate(pinned=Exists(active))
                .filter(state="available")
                .filter(Q(listing__media_tracking_active=True) | Q(pinned=True))
                .order_by("id")
            )
            return tuple(self._backup_reference(asset, execution, now) for asset in assets)

    def _backup_reference(self, asset: MediaAsset, execution: str, now: datetime) -> AnalysisMedia:
        entry = (
            MediaEntry.objects.select_related("capture")
            .filter(asset=asset)
            .order_by("position")
            .first()
        )
        if entry is None:
            raise MediaError("MEDIA_PROVENANCE_UNAVAILABLE", 409)
        return self.acquire(
            asset.listing_id, entry.capture.observation_id, asset.id, "backup", execution, now
        )

    def reconcile_orphans(self, cleanup: Callable[[set[str], int], int], now: datetime) -> int:
        with quota_lock():
            if MediaJob.objects.filter(state="running", lease_until__gt=now).exists():
                return 0
            assets = MediaAsset.objects.exclude(state="removed")
            keys = set(assets.values_list("key", flat=True))
            keys.update(
                key + ".thumb"
                for key in assets.filter(thumbnail_state="ready").values_list("key", flat=True)
            )
            return cleanup(keys, self._policy.lease_seconds)
