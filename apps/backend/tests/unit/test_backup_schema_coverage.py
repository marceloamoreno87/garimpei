"""Schema drift must fail before silently dropping business evidence from a backup."""

import pytest

from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.infra.gateway.operations.schema import SCHEMA
from garimpei.infra.gateway.operations.snapshot_gateway import BusinessSnapshotGateway


def test_snapshot_rejects_a_business_field_missing_from_the_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, fields = SCHEMA["runtime.alerteventdecision"]
    monkeypatch.setitem(
        SCHEMA,
        "runtime.alerteventdecision",
        (model, tuple(name for name in fields if name != "assessment_revision")),
    )
    with pytest.raises(ArchiveInvalid, match="archive_business_schema_incomplete"):
        BusinessSnapshotGateway().capture("schema-drift")
