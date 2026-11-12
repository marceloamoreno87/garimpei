from uuid import UUID

from garimpei.domain.valuation.identity_errors import IdentityNotFound
from garimpei.domain.valuation.identity_ports import IdentityQueries, IdentityView


class ReadIdentityUseCase:
    def __init__(self, queries: IdentityQueries) -> None:
        self._queries = queries

    def execute(self, identity: UUID) -> IdentityView:
        result = self._queries.read(identity)
        if result is None:
            raise IdentityNotFound()
        return result
