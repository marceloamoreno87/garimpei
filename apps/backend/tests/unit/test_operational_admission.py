from garimpei.domain.operations.admission import Admission


def test_new_admission_is_bounded_by_pending_units_and_reserved_bytes() -> None:
    assert Admission(999, 1024, 2 * 1024**3).reason is None
    assert Admission(1000, 1024, 2 * 1024**3).reason == "queue_full"
    assert Admission(0, 10 * 1024**3, 2 * 1024**3).reason == "business_storage_limit"
    assert Admission(0, 1024, 1024**3).reason == "filesystem_reserve"
