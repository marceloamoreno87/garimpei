"""The business backup must retain F23 requests, revisions and consumer links."""

from garimpei.infra.gateway.operations.snapshot_gateway import _validate_schema_coverage


def test_f23_persistence_is_covered_by_the_business_backup_contract() -> None:
    _validate_schema_coverage()
