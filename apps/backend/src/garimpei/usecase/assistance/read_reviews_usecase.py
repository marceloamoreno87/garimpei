from uuid import UUID

from garimpei.domain.assistance.ports import AssistanceQueries


class ReadReviewsUseCase:
    def __init__(self, queries: AssistanceQueries) -> None:
        self._queries = queries

    def execute(self, identity: UUID) -> dict[str, object]:
        return self._queries.listing(identity)
