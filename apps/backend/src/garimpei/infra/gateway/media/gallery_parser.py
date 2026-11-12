"""Only inspect photo fields of the verified listing object, never recommendations."""

from collections.abc import Mapping
from typing import cast
from urllib.parse import urlsplit

from garimpei.domain.media.media import Manifest, Photo, Variant


def mapping(value: object) -> dict[str, object]:
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def variants(photo: dict[str, object]) -> tuple[Variant, ...]:
    rows = [photo] + [
        mapping(photo.get(key))
        for key in (
            "image",
            "image_uri",
            "image_full_screen",
            "image_fullscreen",
            "image_large",
            "image_thumbnail",
        )
    ]
    extra = photo.get("images")
    if isinstance(extra, list):
        rows += [mapping(v) for v in extra[:4]]
    result = []
    for row in rows:
        raw = row.get("uri") or row.get("url") or row.get("image_uri")
        if not isinstance(raw, str) or len(raw) > 8192:
            continue
        parsed = urlsplit(raw)
        if parsed.scheme != "https" or parsed.username or parsed.password or not parsed.hostname:
            continue
        width, height = row.get("width"), row.get("height")
        value = Variant(
            raw,
            width if isinstance(width, int) and width > 0 else None,
            height if isinstance(height, int) and height > 0 else None,
        )
        if value not in result:
            result.append(value)
    return tuple(sorted(result, key=lambda variant: variant.area, reverse=True))


def extract_gallery(row: Mapping[str, object], detail: bool) -> Manifest:
    primary = mapping(row.get("primary_listing_photo"))
    raw = row.get("listing_photos")
    photos = raw if isinstance(raw, list) else mapping(raw).get("nodes")
    recognized = isinstance(photos, list) and detail
    records = [mapping(v) for v in photos[:100]] if isinstance(photos, list) else []
    primary_key = photo_identity(primary)
    if primary and not any(primary_key and photo_identity(p) == primary_key for p in records):
        records.insert(0, primary)
    result: list[Photo] = []
    limited = isinstance(photos, list) and len(photos) > 100
    for position, photo in enumerate(records):
        found = variants(photo)
        if primary_key and photo_identity(photo) == primary_key:
            found = tuple(
                sorted(set(found + variants(primary)), key=lambda v: v.area, reverse=True)
            )
        limited = limited or len(found) > 3
        if not found:
            continue
        key = photo_identity(photo) or f"uncorrelated-{position}"
        if not any(p.key == key for p in result):
            result.append(
                Photo(
                    key,
                    found[:3],
                    key == primary_key or position == 0,
                    photo_identity(photo) is not None,
                )
            )
    if not result:
        return (
            Manifest("none", (), True, "", 0)
            if recognized and photos == [] and not primary
            else Manifest()
        )
    complete = recognized and not limited and len(result) == len(records)
    return Manifest(
        "present",
        tuple(result),
        complete,
        "" if complete else "media_candidate_limit" if limited else "media_gallery_partial",
        max(len(records), len(photos)) if isinstance(photos, list) and recognized else None,
    )


def photo_identity(photo: dict[str, object]) -> str | None:
    value = photo.get("id")
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return None
    key = str(value)
    return key if 0 < len(key) <= 200 else None
