from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.listing import Evidence, Match
from garimpei.domain.listing.scope import Scope


@dataclass(frozen=True)
class Observation:
    id: UUID
    observed_at: datetime
    revision: int
    scope_key: str
    evidence: Evidence
    coverage: Coverage
    provenance: tuple[tuple[str, str], ...]
    interests: tuple[Match, ...]


@dataclass(frozen=True)
class ListingView:
    id: UUID
    source: str
    external_id: str
    canonical_url: str
    first_seen_at: datetime
    origin: str
    observation: Observation
    scope_current: bool
    current_coverage: Coverage
    applicable_freight: Decimal | None
    stale_reason: str | None
    last_valid_observation: Observation | None
    currency: str = "BRL"


@dataclass(frozen=True)
class Change:
    sequence: int
    id: UUID
    kind: str
    listing_id: UUID
    observation_id: UUID
    occurred_at: datetime
    silent: bool
    coverage: Coverage
    price: Decimal | None
    previous_price: Decimal | None
    previous_observation_id: UUID | None
    previous_observed_at: datetime | None
    currency: str = "BRL"
    publication_order: int | None = None


@dataclass(frozen=True)
class ChangePage:
    events: tuple[Change, ...]
    cursor: int | None


@dataclass(frozen=True)
class CollectionStatus:
    phase: str = "scheduled"
    scope_current: bool = False
    initial_completed_at: datetime | None = None
    last_success_at: datetime | None = None
    last_attempt_at: datetime | None = None
    next_attempt_at: datetime | None = None
    reason: str | None = None
    window_start: datetime | None = None
    window_end: datetime | None = None
    window_proofs: tuple[tuple[str, str], ...] = ()
    monitoring_started_at: datetime | None = None
    access_suspended: bool = False


class ListingReader(Protocol):
    def listing(self, identity: UUID, scope: Scope | None) -> ListingView | None: ...


class ChangesReader(Protocol):
    def changes(self, after: int | None, limit: int) -> ChangePage: ...


class StatusReader(Protocol):
    def status(self, scope: Scope | None) -> CollectionStatus: ...
