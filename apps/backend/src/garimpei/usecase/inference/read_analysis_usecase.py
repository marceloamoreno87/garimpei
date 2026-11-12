from uuid import UUID

from garimpei.domain.inference.ports import InferenceQueries


class ReadAnalysisUseCase:
    def __init__(self, queries: InferenceQueries) -> None:
        self._queries = queries

    def execute(self, identity: UUID) -> dict[str, object]:
        return self._queries.analysis(identity)
