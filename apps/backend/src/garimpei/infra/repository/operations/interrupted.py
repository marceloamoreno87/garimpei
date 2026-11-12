"""Called only under the exclusive maintenance lock; no creator can still own these rows."""

from django.db import transaction
from django.db.models import F
from django.utils.timezone import now

from garimpei.domain.operations.ports import ProgressRecorder
from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway
from garimpei.infra.persistence.media_models import MediaReference
from garimpei.infra.persistence.operations_models import BackupRecord, BackupSchedule


def recover_interrupted(
    installation: str, archives: ArchiveGateway, progress: ProgressRecorder | None = None
) -> None:
    rows = BackupRecord.objects.filter(installation=installation, state="creating")
    for row in rows:
        # A final file without the catalog commit is never advertised as a complete copy.
        archives.discard_unpublished(row.id, row.kind)
        with transaction.atomic():
            BackupRecord.objects.filter(id=row.id, state="creating").update(
                state="failed", reason="operation_interrupted", finished_at=now()
            )
            MediaReference.objects.filter(
                consumer="backup", execution=str(row.id), released_at__isnull=True
            ).update(released_at=now())
            _backup_failure(row, installation, progress)


def _backup_failure(
    row: BackupRecord, installation: str, progress: ProgressRecorder | None
) -> None:
    if row.kind != "backup":
        return
    BackupSchedule.objects.filter(installation=installation).update(
        failures=F("failures") + 1, last_failure_at=now()
    )
    if progress:
        progress.failure("maintenance", "automatic-backup", 1, "operation_interrupted", now())
