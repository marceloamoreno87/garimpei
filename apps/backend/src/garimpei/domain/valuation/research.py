from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from garimpei.domain.listing.listing import Candidate
from garimpei.domain.listing.ports import Page, SourceFailure
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.valuation.research_limits import ResearchLimits


@dataclass(frozen=True)
class ResearchUnit:
    id: UUID
    generation: int
    scope: Scope
    query: Search
    product_key: str
    limits: ResearchLimits
    cursor: str | None
    pages: int
    pending: tuple[str, ...]


class ResearchStore(Protocol):
    def claim(self) -> ResearchUnit | None: ...
    def page(self, unit: ResearchUnit, page: Page) -> ResearchUnit | None: ...
    def detail(self, unit: ResearchUnit, candidate: Candidate) -> ResearchUnit | None: ...
    def failed(self, unit: ResearchUnit, failure: SourceFailure) -> None: ...
    def yield_slice(self, unit: ResearchUnit) -> None: ...
