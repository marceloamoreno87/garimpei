import pytest

from tests.factories.operations_lab import _validate_paired_workload


@pytest.mark.parametrize(
    "first,second", [(None, None), (None, 1), (1, None), (False, False), (0, 0), (1, 2), ("x", "x")]
)
def test_unidentified_or_different_loads_cannot_count_as_a_matched_control(
    first: object, second: object
) -> None:
    with pytest.raises(RuntimeError):
        _validate_paired_workload({"workload_signature": first}, {"workload_signature": second})


def test_identical_identified_loads_are_accepted() -> None:
    _validate_paired_workload({"workload_signature": 123}, {"workload_signature": 123})
