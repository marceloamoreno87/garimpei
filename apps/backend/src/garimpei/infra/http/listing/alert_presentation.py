from uuid import UUID

from garimpei.domain.alert.diagnostic import AlertDiagnosticReadFailed
from garimpei.usecase.alert.read_alert_diagnostic_usecase import ReadAlertDiagnosticUseCase


def alert_context(
    reader: ReadAlertDiagnosticUseCase | None, listing_id: UUID, observation_id: UUID | None
) -> dict[str, object]:
    if reader is None:
        return dict(alert=None, alert_failed=True)
    try:
        return dict(alert=reader.execute(listing_id, observation_id), alert_failed=False)
    except AlertDiagnosticReadFailed:
        return dict(alert=None, alert_failed=True)
