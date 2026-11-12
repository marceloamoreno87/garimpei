from datetime import UTC, datetime, timedelta

from garimpei.domain.listing.window import PublicationWindow


def test_window_is_48_hours_inclusive_and_missing_dates_stay_unknown() -> None:
    end = datetime(2026, 11, 11, 12, tzinfo=UTC)
    window = PublicationWindow.ending_at(end)
    assert window.start == end - timedelta(hours=48)
    assert window.contains(window.start) is True
    assert window.contains(end) is True
    assert window.contains(window.start - timedelta(microseconds=1)) is False
    assert window.contains(end + timedelta(microseconds=1)) is False
    assert window.contains(None) is None


def test_legacy_city_only_coordinates_remain_unavailable() -> None:
    from garimpei.domain.listing.coverage import coverage
    from garimpei.domain.listing.geography import Point
    from garimpei.domain.listing.listing import Evidence
    from garimpei.infra.repository.listing.mapper import decode_evidence, encode_evidence

    raw = encode_evidence(Evidence(pickup=True, location=Point(0, 0, None, "São Paulo", "SP")))
    assert raw["location"] is not None
    raw["location"].pop("coordinates_known")
    recovered = decode_evidence(raw)
    projection = coverage(Point(-23.55, -46.63, None, "São Paulo", "SP"), "01001000", recovered)
    assert projection.pickup == "unknown"
    assert projection.distance_km is None
