from unittest.mock import patch

from garimpei.main import build_monitoring_handler


def test_f03_composition_does_not_eagerly_read_optional_research_schema() -> None:
    # During additive migration, only F03 tables exist. Optional tracking is lazy.
    with patch(
        "garimpei.main.build_read_comparable_research",
        side_effect=AssertionError("Optional research factory ran during F03 composition"),
    ) as factory:
        build_monitoring_handler()
    factory.assert_not_called()
