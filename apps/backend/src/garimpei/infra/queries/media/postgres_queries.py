from uuid import UUID

from django.db.models import Prefetch

from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.media import MediaFile, MediaGallery
from garimpei.infra.persistence.listing_models import ListingObservation
from garimpei.infra.persistence.media_models import MediaAsset, MediaCapture, MediaEntry
from garimpei.infra.repository.media.mapper import photo_view


class PostgresMediaQueries:
    def gallery(
        self, listing: UUID, observation: UUID, revision: int | None = None
    ) -> MediaGallery:
        if not ListingObservation.objects.filter(id=observation, listing_id=listing).exists():
            raise MediaError("MEDIA_NOT_FOUND", 404)
        capture = (
            MediaCapture.objects.filter(observation_id=observation)
            .prefetch_related(
                Prefetch(
                    "entries",
                    queryset=MediaEntry.objects.select_related("asset").order_by("position"),
                )
            )
            .first()
        )
        if capture is None:
            return MediaGallery(listing, observation)
        if revision is not None and capture.revision != revision:
            raise MediaError("MEDIA_REVISION_CONFLICT", 409)
        return self._gallery(capture, listing, observation)

    @staticmethod
    def _gallery(capture: MediaCapture, listing: UUID, observation: UUID) -> MediaGallery:
        return MediaGallery(
            listing,
            observation,
            capture.id,
            capture.revision,
            capture.presence,
            capture.state,
            capture.reason,
            capture.complete,
            capture.known_count,
            tuple(photo_view(e) for e in capture.entries.all()),
        )

    def galleries(self, pairs: tuple[tuple[UUID, UUID], ...]) -> dict[UUID, MediaGallery]:
        """Trusted snapshot identities: two queries, independent of the inventory size."""
        listings = {observation: listing for listing, observation in pairs}
        result = {observation: MediaGallery(listing, observation) for listing, observation in pairs}
        captures = MediaCapture.objects.filter(observation_id__in=listings).prefetch_related(
            Prefetch(
                "entries", queryset=MediaEntry.objects.select_related("asset").order_by("position")
            )
        )
        for capture in captures:
            result[capture.observation_id] = self._gallery(
                capture, listings[capture.observation_id], capture.observation_id
            )
        return result

    def file(self, listing: UUID, version: UUID, variant: str) -> MediaFile:
        asset = MediaAsset.objects.filter(id=version, listing_id=listing).first()
        if asset is None or variant not in {"original", "miniatura"}:
            raise MediaError("MEDIA_NOT_FOUND", 404)
        if asset.state in {"removing", "removed"}:
            raise MediaError("MEDIA_REMOVED", 410)
        if variant == "miniatura":
            if asset.thumbnail_state != "ready":
                raise MediaError("MEDIA_THUMBNAIL_PENDING")
            return MediaFile(
                asset.id,
                asset.key + ".thumb",
                "image/webp",
                asset.thumbnail_hash,
                asset.thumbnail_bytes,
            )
        if asset.state != "available":
            raise MediaError("MEDIA_FILE_UNAVAILABLE")
        return MediaFile(asset.id, asset.key, asset.mime, asset.sha256, asset.byte_count)


def availability_overlay(gallery: MediaGallery | None) -> MediaGallery | None:
    from dataclasses import replace

    if gallery is None:
        return None
    states = dict(
        MediaAsset.objects.filter(
            id__in=[p.version_id for p in gallery.photos if p.version_id]
        ).values_list("id", "state")
    )
    return replace(
        gallery,
        photos=tuple(
            replace(p, state=states.get(p.version_id, p.state) if p.version_id else p.state)
            for p in gallery.photos
        ),
    )
