from garimpei.domain.navigation.ports import NavigationQueries
from garimpei.domain.navigation.read_models import NavigationStatus


class ReadNavigationStatusUseCase:
    def __init__(self, queries: NavigationQueries) -> None:
        self._queries = queries

    def execute(self) -> NavigationStatus:
        return self._queries.status()
