"""Recovery imports data only into an empty, owned disposable evaluation instance."""

import json
import os
from datetime import datetime
from pathlib import Path
from uuid import UUID

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from garimpei.config.env import RuntimeConfig
from garimpei.domain.operations.errors import OperationsError
from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway, ArchiveInvalid
from garimpei.infra.gateway.operations.snapshot_gateway import BusinessSnapshotGateway
from garimpei.infra.persistence.alert_models import AlertFeedCursor, AlertIntent
from garimpei.infra.persistence.integration_models import IntegrationSettings
from garimpei.infra.persistence.listing_models import CollectionState
from garimpei.infra.persistence.operations_models import OperationalUnit, RecoveryBarrier
from garimpei.infra.persistence.valuation_models import ValuationWork
from garimpei.infra.repository.operations.maintenance_lock import maintenance_lock
from garimpei.infra.runtime.manifest import read_manifest


class RestoreBackupGateway:
    def __init__(
        self,
        config: RuntimeConfig,
        recovery_file: Path,
        archives: ArchiveGateway,
        snapshot: BusinessSnapshotGateway,
    ) -> None:
        self._config, self._file = config, recovery_file
        self._archives, self._snapshot = archives, snapshot

    def execute(self, archive: Path, *, isolated: bool) -> UUID:
        self._validate_target(isolated)
        try:
            metadata, files = self._archives.read(archive)
            self._snapshot.validate(metadata, files)
            backup_id = UUID(str(metadata["id"]))
            snapshot_at = datetime.fromisoformat(str(metadata["snapshot_at"]))
            if snapshot_at.tzinfo is None:
                raise ArchiveInvalid("archive_snapshot_invalid")
        except (ArchiveInvalid, ValueError, KeyError):
            raise OperationsError("restore_archive_invalid", 400) from None
        with maintenance_lock():
            if not self._snapshot.is_empty():
                raise OperationsError("restore_requires_empty_disposable_eval")
            self._block_dispatch(backup_id, snapshot_at)
            self._import(files, metadata)
            RecoveryBarrier.objects.filter(installation=self._config.environment_id).update(
                evidence={
                    "data_integrity": "verified",
                    "source_installation": str(metadata["installation"]),
                }
            )
        return backup_id

    def _validate_target(self, isolated: bool) -> None:
        manifest = read_manifest(self._config.directory)
        if not isolated or self._config.environment != "eval" or manifest is None:
            raise OperationsError("restore_requires_owned_disposable_eval")
        if (
            not manifest["disposable"]
            or manifest["session_kind"] != "synthetic"
            or manifest["checkout"] != str(self._config.root)
            or manifest["environment_id"] != self._config.environment_id
        ):
            raise OperationsError("restore_requires_owned_disposable_eval")

    def _block_dispatch(self, backup_id: UUID, snapshot_at: datetime) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self._file.exists():
            with self._file.open("x") as output:
                os.fchmod(output.fileno(), 0o600)
                json.dump(
                    {
                        "backup_id": str(backup_id),
                        "snapshot_at": snapshot_at.isoformat(),
                        "state": "blocked",
                    },
                    output,
                )
                output.flush()
                os.fsync(output.fileno())
        RecoveryBarrier.objects.update_or_create(
            installation=self._config.environment_id,
            defaults={
                "backup_id": backup_id,
                "snapshot_at": snapshot_at,
                "restored_at": timezone.now(),
                "state": "blocked",
            },
        )

    def _import(self, files: dict[str, bytes], metadata: dict[str, object]) -> None:
        with transaction.atomic():
            self._snapshot.restore(files, metadata)
            AlertFeedCursor.objects.update(dispatch_suspended=True)
            AlertIntent.objects.update(lease_until=None)
            CollectionState.objects.update(
                lease_until=None, access_suspended=True, generation=F("generation") + 1
            )
            ValuationWork.objects.update(lease_until=None)
            IntegrationSettings.objects.update(
                alerts_enabled=False,
                facebook_file="",
                facebook_login_state="",
                facebook_login_request=None,
                facebook_login_requested_at=None,
                facebook_saved_at=None,
                facebook_expires_at=None,
                whatsapp_configured=False,
            )
            OperationalUnit.objects.update(
                installation=self._config.environment_id,
                suspended=True,
                reason="recovery_barrier",
                generation=F("generation") + 1,
            )
