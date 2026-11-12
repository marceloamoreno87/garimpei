from datetime import UTC, datetime, timedelta

import pytest

from garimpei.domain.alert.first_eligibility import first_eligibility, publication_status

NOW = datetime(2026, 11, 12, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    ("age", "expected"),
    [
        (timedelta(hours=48), "eligible"),
        (timedelta(hours=48, microseconds=1), "publication_expired"),
        (timedelta(), "eligible"),
        (timedelta(seconds=-1), "publication_future"),
    ],
)
def test_publication_window_is_inclusive(age: timedelta, expected: str) -> None:
    assert first_eligibility(NOW - age, "facebook.creation_time", NOW, (), False) == expected


def test_no_collection_timestamp_or_untrusted_date_can_authorize() -> None:
    assert publication_status(None, None, NOW) == "missing"
    assert first_eligibility(NOW, None, NOW, (), False) == "publication_untrusted"
    assert (
        publication_status(NOW.replace(tzinfo=None), "facebook.creation_time", NOW) == "untrusted"
    )


def test_manual_action_requires_independent_automatic_input() -> None:
    assert first_eligibility(NOW, "fixture.published_at", NOW, (), True) == "manual_change_only"
    assert (
        first_eligibility(NOW, "fixture.published_at", NOW, ("condition_excluded",), False)
        == "condition_excluded"
    )


def test_invalid_source_evidence_is_distinct_from_absent_publication() -> None:
    assert publication_status(None, "fixture.published_at.invalid", NOW) == "untrusted"
    assert publication_status(None, None, NOW) == "missing"


def test_adapters_derive_absolute_publication_without_trusting_page_flags() -> None:
    from garimpei.infra.gateway.listing.fixture_source import _candidate

    for raw, expected in (
        (None, "missing"),
        ("há 2 horas", "untrusted"),
        ("2026-11-12T12:00:00", "untrusted"),
        ("2026-11-12T09:00:00-03:00", "trusted"),
    ):
        candidate = _candidate(
            {
                "url": "https://www.facebook.com/marketplace/item/16001/",
                "published_at": raw,
                "published_at_source": "fixture.published_at",
            },
            "detail",
        )
        assert (
            publication_status(
                candidate.evidence.published_at, candidate.evidence.published_at_source, NOW
            )
            == expected
        )


def test_untrusted_publication_survives_consolidation_and_persistence_mapping() -> None:
    from uuid import uuid4

    from garimpei.domain.listing.consolidation import consolidate
    from garimpei.domain.listing.scope import Scope
    from garimpei.infra.gateway.listing.fixture_source import _candidate
    from garimpei.infra.repository.listing.mapper import decode_evidence, encode_evidence

    source = _candidate(
        {"url": "https://www.facebook.com/marketplace/item/16001/", "published_at": "há 2 horas"},
        "detail",
    )
    evidence = consolidate(
        [source], Scope(uuid4(), "facebook_marketplace", "01001000", 1, "test", ())
    ).evidence
    restored = decode_evidence(encode_evidence(evidence))
    assert (
        publication_status(restored.published_at, restored.published_at_source, NOW) == "untrusted"
    )
