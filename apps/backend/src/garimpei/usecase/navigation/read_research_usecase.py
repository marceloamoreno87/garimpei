from uuid import UUID

from garimpei.domain.navigation.ports import NavigationQueries
from garimpei.domain.navigation.read_models import ResearchStatus


class ReadResearchUseCase:
    def __init__(self, queries: NavigationQueries) -> None:
        self._queries = queries

    def execute(self, work_id: UUID) -> ResearchStatus:
        return self._queries.research(work_id)
