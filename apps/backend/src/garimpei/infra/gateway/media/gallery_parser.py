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
    return tuple(result[:3])


def extract_gallery(row: Mapping[str, object], detail: bool) -> Manifest:
    primary = mapping(row.get("primary_listing_photo"))
    raw = row.get("listing_photos")
    photos = raw if isinstance(raw, list) else mapping(raw).get("nodes")
    recognized = isinstance(photos, list) and detail
    records = [mapping(v) for v in photos[:100]] if isinstance(photos, list) else []
    primary_key = str(primary.get("id", ""))
    if primary and not any(primary_key and str(p.get("id", "")) == primary_key for p in records):
        records.insert(0, primary)
    result = []
    for position, photo in enumerate(records):
        found = variants(photo)
        if not found:
            continue
        key = str(photo.get("id") or f"uncorrelated-{position}")[:200]
        result.append(Photo(key, found, key == primary_key or position == 0, bool(photo.get("id"))))
    if not result:
        return (
            Manifest("none", (), True, "", 0)
            if recognized and photos == [] and not primary
            else Manifest()
        )
    complete = recognized and len(result) == len(records)
    return Manifest(
        "present",
        tuple(result),
        complete,
        "" if complete else "media_gallery_partial",
        len(records) if recognized else None,
    )
