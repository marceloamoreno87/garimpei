from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class WorkView:
    id: UUID
    revision: int
    interest: str
    front: str
    term: str
    original_term: str
    catalog_version: str
    phase: str
    reason: str
    last_progress_at: datetime | None
    next_attempt_at: datetime | None
    pages: int
    details: int
    pending: int
    buffered: int = 0
    purpose: str = "active"
    observations: tuple[UUID, ...] = ()


@dataclass(frozen=True)
class NavigationStatus:
    observed_at: datetime
    works: tuple[WorkView, ...]
    page_limit: int = 100
    term_limit: int = 3


@dataclass(frozen=True)
class EvidenceView:
    url: str
    excerpt: str
    observed_at: datetime
    source: str
    external_id: str


@dataclass(frozen=True)
class SuggestionView:
    id: UUID
    term: str
    original_term: str
    relation: str
    observed_at: datetime
    evidence: tuple[EvidenceView, ...]
    revision: int
    limit_reason: str = ""


@dataclass(frozen=True)
class SuggestionBudget:
    reason: str
    message: str
    next_at: datetime | None
    pages: int
    details: int
    page_limit: int
    detail_limit: int
    seconds_limit: int
    interval_seconds: int
    suggestion_count: int
    suggestion_limit: int
    evidence_limit: int
    capacity_reason: str
    capacity_message: str


@dataclass(frozen=True)
class SuggestionPage:
    items: tuple[SuggestionView, ...]
    page: int
    has_next: bool
    budget: SuggestionBudget | None = None


@dataclass(frozen=True)
class ResearchLimits:
    page_limit: int
    term_limit: int


@dataclass(frozen=True)
class ResearchStatus:
    work_id: UUID
    scope_revision: int
    source: str
    origin_interest: str
    canonical_term: str
    purpose: str
    phase: str
    reason: str
    scope_key: str
    context_hash: str
    window_start: datetime | None
    window_end: datetime | None
    limits: ResearchLimits
    pages: int
    details: int
    shared_pages: int
    observations: tuple[UUID, ...]
    historical: bool
