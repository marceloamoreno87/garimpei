from dataclasses import asdict
from datetime import datetime
from uuid import uuid4

from django.db import transaction

from garimpei.domain.media.media import Manifest
from garimpei.domain.media.policy import MediaPolicy
from garimpei.infra.persistence.listing_models import ListingObservation
from garimpei.infra.persistence.media_models import MediaAsset, MediaCapture, MediaEntry, MediaJob


@transaction.atomic
def create_capture(
    observation: ListingObservation, manifest: Manifest, policy: MediaPolicy, now: datetime
) -> MediaCapture:
    capture, created = MediaCapture.objects.get_or_create(
        observation=observation,
        defaults={
            "id": uuid4(),
            "observed_at": observation.observed_at,
            "presence": manifest.presence,
            "complete": manifest.complete,
            "source_complete": manifest.complete,
            "reason": manifest.reason,
            "known_count": manifest.known_count,
            "state": "ready"
            if manifest.presence == "none"
            else "pending"
            if policy.budget_bytes
            else "configuration_required",
        },
    )
    if not created:
        return capture
    bounded = manifest.bounded(policy.max_photos)
    capture.complete, capture.reason = bounded.complete, bounded.reason
    capture.source_complete = bounded.complete
    capture.known_count = bounded.known_count
    capture.save(update_fields=["complete", "source_complete", "reason", "known_count"])
    for position, photo in enumerate(bounded.photos):
        photo_key = photo.key if photo.correlated else f"{capture.id}:{position}"
        prior = (
            MediaAsset.objects.filter(
                listing_id=observation.listing_id, photo_key=photo_key, state="available"
            )
            .order_by("-obtained_at")
            .first()
            if photo.correlated
            else None
        )
        entry = MediaEntry.objects.create(
            id=uuid4(),
            capture=capture,
            photo_key=photo_key,
            position=position,
            primary=position == 0,
            correlated=photo.correlated,
            candidates=[asdict(v) for v in photo.ordered_variants[:3]],
            asset=prior,
        )
        MediaJob.objects.create(id=uuid4(), entry=entry, kind="download", next_at=now)
    return capture
