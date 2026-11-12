from datetime import timedelta

from django.utils import timezone

from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway
from garimpei.infra.persistence.operations_models import BackupRecord, OperationalDiagnostic


def prune_operations(installation: str, archives: ArchiveGateway) -> dict[str, int]:
    now = timezone.now()
    diagnostics = OperationalDiagnostic.objects.filter(unit__installation=installation).order_by(
        "-created_at"
    )
    disposable = [
        row.id
        for position, row in enumerate(diagnostics)
        if not row.protected and (position >= 10000 or row.created_at < now - timedelta(days=7))
    ]
    count, _ = OperationalDiagnostic.objects.filter(id__in=disposable).delete()
    expired = BackupRecord.objects.filter(
        installation=installation,
        kind="export",
        state="completed",
        finished_at__lt=now - timedelta(days=1),
        transferring=0,
    )
    exports = 0
    for record in expired:
        archives.resolve(record.file_key).unlink(missing_ok=True)
        record.state, record.reason = "removed", "export_expired"
        record.save(update_fields=["state", "reason"])
        exports += 1
    return {"diagnostics": count, "expired_exports": exports}
