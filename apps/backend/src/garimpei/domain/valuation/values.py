from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from garimpei.domain.listing.listing import Evidence

METHOD = "median-brl-v1"


@dataclass(frozen=True)
class Comparable:
    listing_id: UUID
    source: str
    external_id: str
    title: str
    url: str
    price: Decimal | None
    observed_at: datetime
    revision: int
    evidence: Evidence
    price_kind: Literal["announced"] = "announced"


@dataclass(frozen=True)
class Resale:
    price: Decimal | None
    reason: str | None
    comparables: tuple[Comparable, ...]
    before: int
    after: int
    valid_until: datetime | None

    @property
    def state(self) -> str:
        return "disponivel" if self.price is not None else "estimativa_indisponivel"


@dataclass(frozen=True)
class NewQuote:
    product: str
    source: str
    external_id: str
    title: str
    url: str
    price: Decimal
    observed_at: datetime
    currency: str = "BRL"
    available: bool = True
    price_kind: Literal["announced"] = "announced"


@dataclass(frozen=True)
class NewReference:
    state: str
    quote: NewQuote | None = None
    diagnostic: str | None = None
    failures: int = 0


@dataclass(frozen=True)
class Valuation:
    id: UUID | None
    listing_id: UUID
    revision: int
    input_revision: int
    product: str | None
    evaluated_at: datetime
    resale: Resale
    new: NewReference
    method: str = METHOD
    currency: str = "BRL"
    origin_diagnostic: str | None = None
