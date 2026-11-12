from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal
from uuid import UUID

Presence = Literal["unknown", "none", "present"]


@dataclass(frozen=True)
class Variant:
    url: str
    width: int | None = None
    height: int | None = None

    @property
    def area(self) -> int:
        return (self.width or 0) * (self.height or 0)


@dataclass(frozen=True)
class Photo:
    key: str
    variants: tuple[Variant, ...]
    primary: bool = False
    correlated: bool = True

    @property
    def ordered_variants(self) -> tuple[Variant, ...]:
        return tuple(sorted(self.variants, key=lambda v: v.area, reverse=True))


@dataclass(frozen=True)
class Manifest:
    presence: Presence = "unknown"
    photos: tuple[Photo, ...] = ()
    complete: bool = False
    reason: str = "media_not_verified"
    known_count: int | None = None

    def bounded(self, limit: int) -> "Manifest":
        ordered = tuple(sorted(self.photos, key=lambda p: not p.primary))
        if len(ordered) <= limit:
            return replace(self, photos=ordered)
        return replace(
            self,
            photos=ordered[:limit],
            complete=False,
            reason="media_photo_limit",
            known_count=len(ordered),
        )


@dataclass(frozen=True)
class MediaPhoto:
    key: str
    position: int
    primary: bool
    version_id: UUID | None = None
    state: str = "pending"
    thumbnail_state: str = "pending"
    sha256: str = ""
    mime: str = ""
    width: int = 0
    height: int = 0
    byte_count: int = 0
    obtained_at: datetime | None = None
    reason: str = ""


@dataclass(frozen=True)
class MediaGallery:
    listing_id: UUID
    observation_id: UUID
    capture_id: UUID | None = None
    revision: int = 0
    presence: str = "unknown"
    state: str = "pending"
    reason: str = "media_not_verified"
    complete: bool = False
    known_count: int | None = None
    photos: tuple[MediaPhoto, ...] = ()


@dataclass(frozen=True)
class Transfer:
    data: bytes
    mime: str
    width: int
    height: int
    sha256: str


@dataclass(frozen=True)
class MediaClaim:
    id: UUID
    generation: int
    kind: str
    listing_id: UUID
    observation_id: UUID
    entry_id: UUID
    photo_key: str
    variants: tuple[Variant, ...]
    attempts: int
    asset_id: UUID | None = None


@dataclass(frozen=True)
class MediaFile:
    version_id: UUID
    key: str
    mime: str
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class AnalysisMedia:
    reference_id: UUID
    listing_id: UUID
    observation_id: UUID
    photo: MediaPhoto
