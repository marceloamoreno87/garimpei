from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ResearchDecisionView:
    title: str
    source: str
    url: str
    price: str | None
    observed_at: datetime
    decision: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class InvestigationView:
    id: UUID
    product: str
    term: str
    state: str
    reason: str
    pages: int
    details: int
    attempts: int
    next_attempt_at: datetime | None
    last_progress_at: datetime | None
    shared_targets: int
    requested: str
    observed: str
    decisions: tuple[ResearchDecisionView, ...]
    page_limit: int = 0
    detail_limit: int = 0
    slice_seconds: int = 0
    attempt_limit: int = 0


@dataclass(frozen=True)
class InterestCoverage:
    interest: str
    observed: int
    recognized: int
    gaps: str
    families: tuple[str, ...] = ()
    attributes: tuple[str, ...] = ()
    unsupported: int = 0
    missing: int = 0
    conflicting: int = 0
    unrecognized: int = 0
    excluded: int = 0
    insufficient: int = 0
    not_evaluated: int = 0


@dataclass(frozen=True)
class ResearchDiagnostic:
    enabled: bool
    reason: str
    policy: str | None
    corpus_date: str | None
    corpus_hash: str | None
    coverage: tuple[InterestCoverage, ...]
    investigations: tuple[InvestigationView, ...]
    corpus_version: str | None = None


class ComparableResearchQueries(Protocol):
    def read(self, listing: UUID | None = None) -> ResearchDiagnostic: ...
