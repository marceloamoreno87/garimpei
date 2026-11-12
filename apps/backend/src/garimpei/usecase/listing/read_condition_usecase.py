from uuid import UUID

from garimpei.domain.listing.condition_ports import (
    ConditionNotFound,
    ConditionQueries,
    ConditionView,
)


class ReadConditionUseCase:
    def __init__(self, queries: ConditionQueries) -> None:
        self._queries = queries

    def execute(self, identity: UUID) -> ConditionView:
        view = self._queries.read(identity)
        if view is None:
            raise ConditionNotFound()
        return view
