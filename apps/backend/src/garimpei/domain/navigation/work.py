from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from garimpei.domain.listing.ports import Revisit
from garimpei.domain.listing.scope import Scope, Search


@dataclass(frozen=True)
class Turn:
    id: UUID
    interest: str
    front: str
    last_turn: int
    next_attempt_at: datetime | None

    def attempted(self, order: int) -> "Turn":
        return replace(self, last_turn=order)


@dataclass(frozen=True)
class NavigationUnit:
    turn: Turn
    generation: int
    revision: int
    query: Search
    terms: tuple[str, ...]
    term_index: int
    cursor: str | None
    signatures: tuple[str, ...]
    pages: int
    details: int
    failures: int
    target: Revisit | None
    unit_key: str
    purpose: str = "active"

    @property
    def search(self) -> Search:
        return replace(self.query, term=self.terms[self.term_index])


@dataclass(frozen=True)
class SuggestionUnit:
    id: UUID
    scope: Scope
    query: Search
    relation_key: str
    generation_at: datetime
    pending_id: str
