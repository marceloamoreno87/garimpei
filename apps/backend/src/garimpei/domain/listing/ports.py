from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Candidate, Match
from garimpei.domain.listing.scope import Scope, Search
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot

type Clock = Callable[[], datetime]


@dataclass(frozen=True)
class CollectionPolicy:
    interval: int
    lease: int
    max_pages: int
    retry_base: int
    retry_max: int


@dataclass(frozen=True)
class Attempt:
    cycle_id: UUID
    generation: int


@dataclass(frozen=True)
class Work:
    scope: Scope
    results: frozenset[str]
    scanned: bool


@dataclass(frozen=True)
class Revisit:
    external_id: str
    matches: tuple[Match, ...]
    known: bool = False


@dataclass(frozen=True)
class Page:
    candidates: tuple[Candidate, ...]
    continuation: str | None
    invalid_cards: int = 0
    diagnostic: str | None = None
    window_proof: str | None = None
    rebuilt: bool = False
    traversed_pages: int = 1


class SourceFailure(Exception):
    def __init__(self, reason: str, retry_after: int = 0, *, access: bool = False) -> None:
        super().__init__(reason)
        self.reason = reason
        self.retry_after = retry_after
        self.access = access


class ListingUnavailable(Exception):
    """The source explicitly confirmed unavailability for this requested identity."""

    def __init__(self, external_id: str, evidence: str) -> None:
        super().__init__("listing_unavailable")
        self.external_id = external_id
        self.evidence = evidence


class SupersededAttempt(Exception):
    """The worker no longer owns this attempt or its scope."""


class ListingSource(Protocol):
    def search(self, scope: Scope, query: Search, continuation: str | None) -> Page: ...
    def detail(self, scope: Scope, external_id: str) -> Candidate: ...


class Geocoding(Protocol):
    def resolve(self, cep: str) -> Point | None: ...


class ConfigurationReader(Protocol):
    def execute(self) -> MonitoringSnapshot: ...


class CollectionStore(Protocol):
    def reconcile(self, policy: CollectionPolicy) -> None: ...
    def begin(self, attempt: Attempt) -> Work: ...
    def stage(self, attempt: Attempt, key: str, candidates: tuple[Candidate, ...]) -> None: ...
    def record(
        self,
        attempt: Attempt,
        key: str,
        failure: SourceFailure | None,
        window_proof: str | None = None,
    ) -> None: ...
    def detail_targets(
        self, attempt: Attempt, *, include_known: bool = True
    ) -> tuple[Revisit, ...]: ...
    def set_origin(self, attempt: Attempt, point: Point | None) -> None: ...
    def mark_scanned(self, attempt: Attempt, point: Point | None) -> None: ...
    def publish_batch(self, attempt: Attempt, *, ready_only: bool = False) -> bool: ...
    def finish(self, attempt: Attempt, policy: CollectionPolicy) -> None: ...
