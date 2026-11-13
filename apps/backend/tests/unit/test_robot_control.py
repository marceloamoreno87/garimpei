import pytest

from garimpei.domain.robot.control import effective_state


@pytest.mark.parametrize(
    ("enabled", "active", "unknown", "expected"),
    [
        (True, 0, 0, "enabled"),
        (False, 0, 0, "disabled"),
        (False, 1, 0, "draining"),
        (False, 0, 1, "unknown"),
        (False, 1, 1, "unknown"),
        (True, 1, 1, "unknown"),
    ],
)
def test_requested_state_never_confirms_unknown_termination(
    enabled: bool, active: int, unknown: int, expected: str
) -> None:
    assert effective_state(enabled, active, unknown) == expected
