from uuid import UUID

from garimpei.domain.valuation.research_diagnostic import (
    ComparableResearchQueries,
    ResearchDiagnostic,
)


class ReadComparableResearchDiagnosticUseCase:
    def __init__(self, queries: ComparableResearchQueries) -> None:
        self._queries = queries

    def execute(self, listing: UUID | None = None) -> ResearchDiagnostic:
        return self._queries.read(listing)
