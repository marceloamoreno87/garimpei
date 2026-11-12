from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from unittest.mock import patch

import pytest

from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.policy import MediaPolicy
from garimpei.infra.gateway.media.image_transport import BoundedImageTransport, source_delay
from tests.factories.media import generate_corpus, serve_media


def test_real_bytes_best_quality_and_credential_free_transport() -> None:
    manifest = generate_corpus()
    with serve_media() as (origin, requests):
        transport = BoundedImageTransport(MediaPolicy(), origin)
        result = transport.fetch(origin + "/primary-large.jpg")
        assert result.sha256 == manifest["primary-large.jpg"]["sha256"]
        assert (result.width, result.height) == (1280, 960)
        assert all("Cookie" not in r and "Authorization" not in r for r in requests)
        with pytest.raises(MediaError, match="media_content_rejected"):
            transport.fetch(origin + "/invalid.bin")
        with pytest.raises(MediaError) as failure:
            transport.fetch(origin + "/retry")
        assert failure.value.retry_after == 172800


def test_production_rejects_private_untrusted_and_forged_destinations() -> None:
    transport = BoundedImageTransport(MediaPolicy())
    for url in (
        "http://127.0.0.1/a",
        "https://fbcdn.net.evil.invalid/a",
        "https://user:pass@fbcdn.net/a",
    ):
        with pytest.raises(MediaError, match="media_destination_rejected"):
            transport.fetch(url)
    with patch(
        "garimpei.infra.gateway.media.image_transport.resolve_addresses", return_value=["127.0.0.1"]
    ):
        with pytest.raises(MediaError, match="media_destination_rejected"):
            transport.fetch("https://a.fbcdn.net/a")


def test_retry_after_http_date_and_configured_limits() -> None:
    assert 172798 <= source_delay(format_datetime(datetime.now(UTC) + timedelta(days=2))) <= 172801
    generate_corpus()
    with serve_media() as (origin, _):
        with pytest.raises(MediaError, match="media_file_limit"):
            BoundedImageTransport(MediaPolicy(max_file_bytes=100), origin).fetch(
                origin + "/primary-large.jpg"
            )
        with pytest.raises(MediaError, match="media_pixel_limit"):
            BoundedImageTransport(MediaPolicy(max_pixels=100), origin).fetch(
                origin + "/primary-large.jpg"
            )


def test_parser_ignores_other_listing_and_does_not_claim_absence() -> None:
    from garimpei.infra.gateway.media.gallery_parser import extract_gallery

    row = {
        "id": "1",
        "primary_listing_photo": {
            "id": "p",
            "image": {"uri": "https://a.fbcdn.net/p", "width": 1280, "height": 960},
        },
        "listing_photos": [
            {"id": "p", "image": {"uri": "https://a.fbcdn.net/p"}},
            {"id": "q", "image": {"uri": "https://a.fbcdn.net/q"}},
        ],
        "recommendations": [
            {"id": "2", "primary_listing_photo": {"id": "bad", "uri": "https://a.fbcdn.net/bad"}}
        ],
    }
    found = extract_gallery(row, True)
    assert {p.key for p in found.photos} == {"p", "q"}
    assert extract_gallery({}, True).presence == "unknown"
    assert extract_gallery({"listing_photos": []}, True).presence == "none"


def test_primary_and_gallery_fragments_keep_best_same_photo_variant() -> None:
    from garimpei.infra.gateway.media.gallery_parser import extract_gallery

    row = {
        "primary_listing_photo": {
            "id": "same-photo",
            "image_full_screen": {
                "uri": "https://a.fbcdn.net/large",
                "width": 1600,
                "height": 1200,
            },
        },
        "listing_photos": [
            {
                "id": "same-photo",
                "image": {"uri": "https://a.fbcdn.net/small", "width": 320, "height": 240},
            },
            {
                "id": "additional",
                "image": {"uri": "https://a.fbcdn.net/add", "width": 1000, "height": 800},
            },
        ],
    }
    gallery = extract_gallery(row, True)
    assert len(gallery.photos) == 2
    assert gallery.photos[0].ordered_variants[0].width == 1600
    assert gallery.photos[0].ordered_variants[1].width == 320
    assert gallery.complete


def test_cached_detail_requires_recognized_full_gallery_not_only_primary() -> None:
    from garimpei.infra.gateway.listing.marketplace_browser import _has_listing_gallery
    from garimpei.infra.gateway.listing.relay_parser import JsonObject

    incomplete: tuple[JsonObject, ...] = (
        {
            "id": "1",
            "primary_listing_photo": {"id": "p", "image": {"uri": "https://a.fbcdn.net/p"}},
        },
        {"id": "1", "listing_photos": {}},
        {"id": "1", "listing_photos": {"edges": []}},
    )
    for row in incomplete:
        assert not _has_listing_gallery((row,), "1")
    assert _has_listing_gallery(({"id": "1", "listing_photos": []},), "1")
    assert _has_listing_gallery(({"id": "1", "listing_photos": {"nodes": []}},), "1")
    assert not _has_listing_gallery(({"id": "2", "listing_photos": []},), "1")
