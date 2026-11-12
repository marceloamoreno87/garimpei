"""Bounded, exclusive maintenance. No filesystem path comes from an HTTP caller."""

from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from django.db.models import F
from django.utils import timezone

from garimpei.domain.operations.download import ArchiveDownload
from garimpei.domain.operations.errors import OperationsError
from garimpei.domain.operations.limits import PROFILE
from garimpei.infra.gateway.operations.archive_gateway import (
    ArchiveGateway,
    ArchiveInvalid,
    copy_archive,
    file_hash,
)
from garimpei.infra.gateway.operations.snapshot_gateway import BusinessSnapshotGateway, schema_hash
from garimpei.infra.persistence.operations_models import BackupRecord, BackupSchedule
from garimpei.infra.repository.operations.maintenance_lock import maintenance_lock
from garimpei.infra.repository.operations.retention import prune_operations


class PostgresBackupRepository:
    def __init__(
        self,
        installation: str,
        archives: ArchiveGateway,
        snapshot: BusinessSnapshotGateway,
        restore: "RestoreBackupGateway",
    ) -> None:
        self._installation, self._archives = installation, archives
        self._snapshot, self._restore = snapshot, restore

    def create(self, *, only_due: bool = False) -> UUID | None:
        with maintenance_lock():
            schedule, _ = BackupSchedule.objects.get_or_create(installation=self._installation)
            now = timezone.now()
            if only_due and not _is_due(schedule, now):
                return None
            record = BackupRecord.objects.create(
                id=uuid4(), installation=self._installation, kind="backup", started_at=now
            )
            return self._create_archive(record, schedule)

    def _create_archive(self, record: BackupRecord, schedule: BackupSchedule) -> UUID:
        try:
            moment, files, counts, information = self._snapshot.capture()
            metadata: dict[str, object] = information | {
                "format_version": 1,
                "id": str(record.id),
                "installation": self._installation,
                "snapshot_at": moment.isoformat(),
                "schema_hash": schema_hash(),
                "counts": counts,
                "started_at": record.started_at.isoformat(),
                "limits_profile": PROFILE,
                "backup_interval": 86400,
                "retention": 7,
                "exclusions": [
                    "authentication",
                    "runtime_jobs",
                    "backup_catalog",
                    "transient_media_access_queries",
                ],
                "access_recovery": "Facebook and WhatsApp access must be recovered separately",
            }
            path = self._archives.write("completed", str(record.id), metadata, files)
            self._complete(record, path, {"counts": counts}, moment)
            assert record.finished_at is not None
            schedule.last_success_at, schedule.next_due_at = (
                record.finished_at,
                record.finished_at + timedelta(days=1),
            )
            schedule.failures, schedule.revision = 0, schedule.revision + 1
            schedule.save()
            self._retain()
            return record.id
        except (ArchiveInvalid, OSError, ValueError):
            self._failed(record, schedule)
            raise OperationsError("backup_creation_failed", 507) from None

    def export(self, identity: UUID, request_id: UUID) -> UUID:
        with maintenance_lock():
            existing = BackupRecord.objects.filter(
                installation=self._installation, request_id=request_id
            ).first()
            if existing is not None:
                return _existing_export(existing, identity)
            source = self._find(identity)
            if source.kind != "backup" or source.state != "completed":
                raise OperationsError("backup_not_completed")
            record = BackupRecord.objects.create(
                id=uuid4(),
                installation=self._installation,
                kind="export",
                source=source,
                request_id=request_id,
                started_at=timezone.now(),
            )
            return self._export_archive(record, source)

    def _export_archive(self, record: BackupRecord, source: BackupRecord) -> UUID:
        try:
            original = self._archives.resolve(source.file_key)
            if file_hash(original) != source.sha256:
                raise ArchiveInvalid("archive_checksum_mismatch")
            path = copy_archive(self._archives, original, str(record.id))
            self._complete(record, path, source.scope, source.snapshot_at)
            return record.id
        except (ArchiveInvalid, OSError, ValueError):
            record.state, record.reason, record.finished_at = (
                "failed",
                "export_failed",
                timezone.now(),
            )
            record.save()
            raise OperationsError("export_failed", 507) from None

    def _complete(
        self,
        record: BackupRecord,
        path: Path,
        scope: dict[str, object],
        snapshot_at: "datetime | None",
    ) -> None:
        record.state, record.finished_at = "completed", timezone.now()
        record.file_key = str(path.relative_to(self._archives.root))
        record.sha256, record.size = file_hash(path), path.stat().st_size
        record.scope, record.snapshot_at = scope, snapshot_at
        record.save()

    @staticmethod
    def _failed(record: BackupRecord, schedule: BackupSchedule) -> None:
        now = timezone.now()
        record.state, record.reason, record.finished_at = "failed", "backup_creation_failed", now
        record.save()
        schedule.failures += 1
        schedule.last_failure_at = now
        schedule.save()

    def _retain(self) -> None:
        rows = list(
            BackupRecord.objects.filter(
                installation=self._installation, kind="backup", state="completed"
            ).order_by("-finished_at")
        )
        for row in rows[7:]:
            if row.transferring or row.backuprecord_set.filter(state="creating").exists():
                continue
            self._archives.resolve(row.file_key).unlink(missing_ok=True)
            row.state, row.reason = "removed", "retention_seven_completed"
            row.save(update_fields=["state", "reason"])

    def prune(self) -> dict[str, int]:
        with maintenance_lock():
            self._retain()
            return prune_operations(self._installation, self._archives)

    def _find(self, identity: UUID) -> BackupRecord:
        row = BackupRecord.objects.filter(id=identity, installation=self._installation).first()
        if row is None:
            raise OperationsError("backup_unknown", 404)
        return row

    def catalog(self) -> dict[str, object]:
        rows = BackupRecord.objects.filter(installation=self._installation).order_by("-started_at")
        schedule = BackupSchedule.objects.filter(installation=self._installation).first()
        return {
            "records": [
                {
                    "id": str(r.id),
                    "kind": r.kind,
                    "state": r.state,
                    "reason": r.reason,
                    "started_at": r.started_at,
                    "finished_at": r.finished_at,
                    "format_version": r.format_version,
                    "snapshot_at": r.snapshot_at,
                    "restoration_state": r.restoration_state,
                    "bytes": r.size,
                }
                for r in rows[:100]
            ],
            "next_due_at": schedule.next_due_at if schedule else None,
            "last_success_at": schedule.last_success_at if schedule else None,
            "last_failure_at": schedule.last_failure_at if schedule else None,
        }

    def download(self, identity: UUID) -> ArchiveDownload:
        with maintenance_lock():
            record = self._find(identity)
            if record.kind != "export" or record.state != "completed":
                raise OperationsError("export_not_completed")
            if (
                record.finished_at is None
                or record.finished_at + timedelta(days=1) <= timezone.now()
            ):
                raise OperationsError("export_expired", 410)
            path = self._archives.resolve(record.file_key)
            if file_hash(path) != record.sha256:
                raise OperationsError("export_checksum_mismatch", 503)
            stream = path.open("rb")
            BackupRecord.objects.filter(id=identity).update(transferring=F("transferring") + 1)
            return ArchiveDownload(
                stream, record.size, record.sha256, lambda: self._release_download(identity)
            )

    @staticmethod
    def _release_download(identity: UUID) -> None:
        BackupRecord.objects.filter(id=identity, transferring__gt=0).update(
            transferring=F("transferring") - 1
        )

    def restore(self, archive: str, *, isolated: bool) -> UUID:
        return self._restore.execute(Path(archive), isolated=isolated)

    def verify(self, identity: UUID) -> dict[str, object]:
        record = self._find(identity)
        if record.state != "completed":
            raise OperationsError("backup_not_completed")
        path = self._archives.resolve(record.file_key)
        metadata, files = self._archives.read(path)
        self._snapshot.validate(metadata, files)
        if file_hash(path) != record.sha256:
            raise OperationsError("archive_checksum_mismatch")
        return {
            "id": str(record.id),
            "archive_integrity": "verified",
            "restoration_state": record.restoration_state,
            "dispatch_reconciliation": "not_performed",
        }


def _is_due(schedule: BackupSchedule, now: "datetime") -> bool:
    if schedule.failures >= 3:
        return False
    if (
        schedule.last_failure_at is not None
        and schedule.last_failure_at + timedelta(seconds=300) > now
    ):
        return False
    return schedule.next_due_at is None or schedule.next_due_at <= now


from garimpei.infra.repository.operations.restore_gateway import RestoreBackupGateway  # noqa: E402


def _existing_export(existing: BackupRecord, identity: UUID) -> UUID:
    if existing.source_id != identity:
        raise OperationsError("export_request_conflict")
    return existing.id
