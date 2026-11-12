import pytest

from garimpei.config.env import ConfigurationError, load_navigation_policy


def test_navigation_policy_central_defaults() -> None:
    value = load_navigation_policy()
    assert (
        value.slice_seconds,
        value.slice_pages,
        value.slice_details,
        value.cycle_pages,
        value.cycle_terms,
    ) == (120, 2, 10, 100, 3)
    assert (value.suggestion_seconds, value.suggestion_interval, value.pending_details) == (
        45,
        300,
        500,
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("GARIMPEI_NAV_CYCLE_TERMS", "4"),
        ("GARIMPEI_NAV_SLICE_PAGES", "zero"),
        ("GARIMPEI_NAV_EVIDENCE_LIMIT", "0"),
        ("GARIMPEI_NAV_SUGGESTION_INTERVAL", "40"),
    ],
)
def test_invalid_navigation_policy_rejected(
    monkeypatch: pytest.MonkeyPatch, key: str, value: str
) -> None:
    monkeypatch.setenv(key, value)
    with pytest.raises(ConfigurationError):
        load_navigation_policy()
