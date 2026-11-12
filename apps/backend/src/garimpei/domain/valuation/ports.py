from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from garimpei.domain.valuation.values import Comparable, NewQuote, NewReference, Valuation

Clock = Callable[[], datetime]


class NewSourceFailure(Exception):
    pass


@dataclass(frozen=True)
class WorkInput:
    id: UUID
    listing_id: UUID
    revision: int
    target: Comparable
    candidates: tuple[Comparable, ...]
    previous: NewReference | None


class NewPriceSource(Protocol):
    def offers(self, product: str, now: datetime) -> tuple[NewQuote, ...]: ...


class ValuationStore(Protocol):
    def work(self, identity: UUID) -> WorkInput | None: ...
    def publish(self, work: WorkInput, value: Valuation, due: datetime) -> None: ...
    def failed(self, identity: UUID, now: datetime) -> None: ...


class ValuationReader(Protocol):
    def current(self, identity: UUID, now: datetime) -> Valuation | None: ...
    def historical(self, identity: UUID) -> Valuation | None: ...
