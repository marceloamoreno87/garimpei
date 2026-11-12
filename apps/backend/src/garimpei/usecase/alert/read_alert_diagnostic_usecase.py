from uuid import UUID

from garimpei.domain.alert.diagnostic import AlertDiagnostic, AlertDiagnosticQueries


class ReadAlertDiagnosticUseCase:
    def __init__(self, queries: AlertDiagnosticQueries) -> None:
        self._queries = queries

    def execute(
        self, listing_id: UUID, displayed_observation_id: UUID | None = None
    ) -> AlertDiagnostic | None:
        return self._queries.read(listing_id, displayed_observation_id)
