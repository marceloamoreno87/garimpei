import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from garimpei.domain.listing.geography import Point

MAX_INTEREST_KEY_LENGTH = 400
InterestKind = Literal["category", "product"]
EventKind = Literal["initial_load", "discovered", "price_increased", "price_decreased"]


@dataclass(frozen=True, order=True)
class Match:
    kind: InterestKind
    key: str


@dataclass(frozen=True)
class Evidence:
    title: str | None = None
    description: str | None = None
    condition: str | None = None
    published_at: datetime | None = None
    price: Decimal | None = None
    freight: Decimal | None = None
    freight_cep: str | None = None
    pickup: bool | None = None
    location: Point | None = None
    delivery: bool | None = None
    delivery_cep: str | None = None
    shipping_offered: bool | None = None
    shipping_evidence: str | None = None
    pickup_scope_verified: bool | None = None
    source_available: bool | None = None
    availability_evidence: str | None = None
    image_url: str | None = None
    published_at_source: str | None = None


@dataclass(frozen=True)
class Candidate:
    external_id: str
    evidence: Evidence
    origin: Literal["card", "detail"]
    matches: tuple[Match, ...] = ()


def canonical_url(external_id: str) -> str:
    return f"https://www.facebook.com/marketplace/item/{external_id}/"


def money(label: str | None) -> Decimal | None:
    if label is None:
        return None
    match = re.fullmatch(
        r"R\$\s*([0-9]{1,12}|[0-9]{1,3}(?:\.[0-9]{3}){1,3})(?:,([0-9]{2}))?",
        label.strip(),
    )
    if not match:
        return None
    integer, cents = match.groups()
    return Decimal(f"{integer.replace('.', '')}.{cents or '00'}")


def price_change(previous: Decimal | None, current: Decimal | None) -> EventKind | None:
    if previous is None or current is None or previous == current:
        return None
    return "price_decreased" if current < previous else "price_increased"
