from uuid import UUID

from garimpei.domain.operations.ports import OperationalQueries


class ReadOperationalStatusUseCase:
    def __init__(self, queries: OperationalQueries) -> None:
        self._queries = queries

    def execute(
        self, interest: str | None = None, version: UUID | None = None
    ) -> dict[str, object]:
        return self._queries.read(interest, version)
