from garimpei.domain.media.media import Manifest, MediaPhoto, Photo, Presence, Variant
from garimpei.infra.persistence.media_models import MediaEntry


def encode_manifest(value: Manifest) -> dict[str, object]:
    return {
        "presence": value.presence,
        "complete": value.complete,
        "reason": value.reason,
        "known_count": value.known_count,
        "photos": [
            {
                "key": p.key,
                "primary": p.primary,
                "correlated": p.correlated,
                "variants": [
                    {"url": v.url, "width": v.width, "height": v.height} for v in p.variants
                ],
            }
            for p in value.photos
        ],
    }


def decode_manifest(raw: object) -> Manifest:
    from typing import cast

    if not isinstance(raw, dict):
        return Manifest()
    data = cast(dict[str, object], raw)
    photos = []
    for row in cast(list[dict[str, object]], data.get("photos", [])):
        variants = tuple(
            Variant(
                str(v["url"]),
                int(str(v["width"])) if v.get("width") else None,
                int(str(v["height"])) if v.get("height") else None,
            )
            for v in cast(list[dict[str, object]], row.get("variants", []))
        )
        photos.append(
            Photo(
                str(row["key"]),
                variants,
                bool(row.get("primary")),
                bool(row.get("correlated", True)),
            )
        )
    presence = str(data.get("presence", "unknown"))
    return Manifest(
        cast(Presence, presence) if presence in {"unknown", "none", "present"} else "unknown",
        tuple(photos),
        bool(data.get("complete")),
        str(data.get("reason", "")),
        int(str(data["known_count"])) if data.get("known_count") is not None else None,
    )


def photo_view(entry: MediaEntry) -> MediaPhoto:
    asset = entry.asset
    if asset is None:
        return MediaPhoto(entry.photo_key, entry.position, entry.primary, reason=entry.reason)
    return MediaPhoto(
        entry.photo_key,
        entry.position,
        entry.primary,
        asset.id,
        asset.state,
        asset.thumbnail_state,
        asset.sha256,
        asset.mime,
        asset.width,
        asset.height,
        asset.byte_count,
        asset.obtained_at,
        entry.reason or asset.reason,
    )
