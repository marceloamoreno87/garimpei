"""The operator can identify the protected snapshot and its recovery boundary."""

from datetime import UTC, datetime
from io import StringIO
from unittest.mock import patch
from uuid import UUID

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

IDENTITY = UUID("00000000-0000-4000-8000-000000000017")
SNAPSHOT = datetime(2026, 11, 13, 1, 2, 3, tzinfo=UTC)
RESTORED = datetime(2026, 11, 13, 1, 4, 5, tzinfo=UTC)
FAILED = datetime(2026, 11, 13, 1, 0, 0, tzinfo=UTC)


class EvalConfiguration:
    environment = "eval"


class NamedBackupCatalog:
    def catalog(self) -> dict[str, object]:
        return {
            "last_success_at": SNAPSHOT,
            "next_due_at": RESTORED,
            "last_failure_at": FAILED,
            "recovery": {
                "snapshot_at": SNAPSHOT,
                "restored_at": RESTORED,
                "source_installation": "synthetic-source-installation",
            },
            "records": [
                {
                    "id": str(IDENTITY),
                    "state": "completed",
                    "snapshot_at": SNAPSHOT,
                    "format_version": 1,
                    "restoration_state": "not_tested",
                    "reason": "",
                    "scope": {"counts": {"runtime.listing": 12, "runtime.listingobservation": 22}},
                }
            ],
        }


class RecordedRestore:
    def execute(self, archive: str, *, isolated: bool) -> UUID:
        assert isolated and archive == "/private/synthetic-canary.tar.gz"
        return IDENTITY


def test_restore_output_identifies_snapshot_scope_and_uncovered_interval() -> None:
    output = StringIO()
    with (
        patch(
            "garimpei.infra.persistence.management.commands.operational_backup.load_config",
            return_value=EvalConfiguration(),
        ),
        patch(
            "garimpei.infra.persistence.management.commands.operational_backup.build_backup_repository",
            return_value=NamedBackupCatalog(),
        ),
        patch(
            "garimpei.infra.persistence.management.commands.operational_backup.build_restore_backup",
            return_value=RecordedRestore(),
        ),
    ):
        call_command(
            "operational_backup",
            "restore",
            "--archive",
            "/private/synthetic-canary.tar.gz",
            "--isolated",
            stdout=output,
        )
    text = output.getvalue()
    assert SNAPSHOT.isoformat() in text
    assert RESTORED.isoformat() in text
    assert "synthetic-source-installation" in text
    assert "despacho bloqueado" in text.lower()
    assert "synthetic-canary" not in text


def test_list_output_includes_scope_and_last_failure_separately_from_creation() -> None:
    output = StringIO()
    with patch(
        "garimpei.infra.persistence.management.commands.operational_backup.build_backup_repository",
        return_value=NamedBackupCatalog(),
    ):
        call_command("operational_backup", "list", stdout=output)
    text = output.getvalue()
    assert "12 anúncios" in text and "22 observações" in text
    assert FAILED.isoformat() in text
    assert "not_tested" in text


class NonEvalConfiguration:
    environment = "dev"


def test_dev_restore_is_refused_with_target_guidance_before_repository_io() -> None:
    with (
        patch(
            "garimpei.infra.persistence.management.commands.operational_backup.load_config",
            return_value=NonEvalConfiguration(),
            create=True,
        ),
        patch(
            "garimpei.infra.persistence.management.commands.operational_backup.build_backup_repository",
            side_effect=AssertionError("Repository I/O must not start for a forbidden target"),
        ),
    ):
        with pytest.raises(CommandError, match="eval isolado"):
            call_command(
                "operational_backup",
                "restore",
                "--archive",
                "/private/synthetic.tar.gz",
                "--isolated",
            )
