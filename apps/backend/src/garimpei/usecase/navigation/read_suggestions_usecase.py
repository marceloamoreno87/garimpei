from uuid import UUID

from garimpei.domain.navigation.ports import NavigationQueries
from garimpei.domain.navigation.read_models import SuggestionPage, SuggestionView


class ReadSuggestionsUseCase:
    def __init__(self, queries: NavigationQueries) -> None:
        self._queries = queries

    def execute(self, page: int = 1) -> SuggestionPage:
        return self._queries.suggestions(page)


class ReadSuggestionUseCase:
    def __init__(self, queries: NavigationQueries) -> None:
        self._queries = queries

    def execute(self, identity: UUID) -> SuggestionView:
        return self._queries.suggestion(identity)
