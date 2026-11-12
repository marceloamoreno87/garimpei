from garimpei.domain.inference.ports import InferenceQueries, InferenceStatus


class ReadStatusUseCase:
    def __init__(self, queries: InferenceQueries) -> None:
        self._queries = queries

    def execute(self) -> InferenceStatus:
        return self._queries.status()
