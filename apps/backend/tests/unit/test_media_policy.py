from garimpei.domain.media.media import Manifest, Photo, Variant
from garimpei.domain.media.policy import MediaPolicy


def test_primary_priority_and_best_variant_are_explicit() -> None:
    small = Variant("https://a.fbcdn.net/small", 10, 10)
    large = Variant("https://a.fbcdn.net/large", 100, 100)
    photo = Photo("p", (small, large), True)
    assert photo.ordered_variants == (large, small)
    bounded = Manifest("present", (photo, Photo("q", (small,))), True).bounded(1)
    assert bounded.photos == (photo,)
    assert bounded.reason == "media_photo_limit"
    assert not bounded.complete


def test_unknown_and_proven_absence_remain_distinct() -> None:
    assert Manifest().presence == "unknown"
    assert Manifest("none", (), True).presence == "none"
    assert MediaPolicy().budget_bytes is None
    assert MediaPolicy().retry_delay(1, 120) == 120
    assert MediaPolicy().retry_delay(4) is None
