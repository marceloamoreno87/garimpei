from datetime import datetime
from decimal import Decimal
from typing import cast
from uuid import UUID

from garimpei.domain.valuation.values import Comparable, NewQuote, NewReference, Resale, Valuation
from garimpei.infra.repository.listing.mapper import (
    EvidenceRecord,
    decode_evidence,
    encode_evidence,
)


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("Valuation record: expected an object")
    return cast(dict[str, object], value)


def records(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        raise ValueError("Valuation records: expected a list")
    return tuple(mapping(row) for row in value)


def encode_comparable(row: Comparable) -> dict[str, object]:
    return dict(
        listing_id=str(row.listing_id),
        source=row.source,
        external_id=row.external_id,
        title=row.title,
        url=row.url,
        price=str(row.price) if row.price is not None else None,
        observed_at=row.observed_at.isoformat(),
        revision=row.revision,
        evidence=encode_evidence(row.evidence),
        price_kind=row.price_kind,
    )


def decode_comparable(row: dict[str, object]) -> Comparable:
    return Comparable(
        UUID(str(row["listing_id"])),
        str(row["source"]),
        str(row["external_id"]),
        str(row["title"]),
        str(row["url"]),
        Decimal(str(row["price"])) if row["price"] is not None else None,
        datetime.fromisoformat(str(row["observed_at"])),
        int(str(row["revision"])),
        decode_evidence(cast(EvidenceRecord, row["evidence"])),
    )


def encode_quote(row: NewQuote) -> dict[str, object]:
    return dict(
        product=row.product,
        source=row.source,
        external_id=row.external_id,
        title=row.title,
        url=row.url,
        price=str(row.price),
        observed_at=row.observed_at.isoformat(),
        currency=row.currency,
        available=row.available,
        price_kind=row.price_kind,
    )


def decode_quote(row: dict[str, object]) -> NewQuote:
    return NewQuote(
        str(row["product"]),
        str(row["source"]),
        str(row["external_id"]),
        str(row["title"]),
        str(row["url"]),
        Decimal(str(row["price"])),
        datetime.fromisoformat(str(row["observed_at"])),
        str(row["currency"]),
        row["available"] is True,
    )


def encode_valuation(value: Valuation) -> dict[str, object]:
    resale, new = value.resale, value.new
    return dict(
        id=str(value.id),
        listing_id=str(value.listing_id),
        revision=value.revision,
        input_revision=value.input_revision,
        product=value.product,
        evaluated_at=value.evaluated_at.isoformat(),
        method=value.method,
        resale=dict(
            state=resale.state,
            price=str(resale.price) if resale.price is not None else None,
            reason=resale.reason,
            before=resale.before,
            after=resale.after,
            valid_until=resale.valid_until.isoformat() if resale.valid_until else None,
            comparables=[encode_comparable(row) for row in resale.comparables],
        ),
        new=dict(
            state=new.state,
            quote=encode_quote(new.quote) if new.quote else None,
            diagnostic=new.diagnostic,
            failures=new.failures,
        ),
    )


def decode_valuation(raw: dict[str, object]) -> Valuation:
    resale, new = mapping(raw["resale"]), mapping(raw["new"])
    quote = decode_quote(mapping(new["quote"])) if new["quote"] else None
    return Valuation(
        UUID(str(raw["id"])),
        UUID(str(raw["listing_id"])),
        int(str(raw["revision"])),
        int(str(raw["input_revision"])),
        str(raw["product"]) if raw["product"] else None,
        datetime.fromisoformat(str(raw["evaluated_at"])),
        Resale(
            Decimal(str(resale["price"])) if resale["price"] is not None else None,
            str(resale["reason"]) if resale["reason"] else None,
            tuple(decode_comparable(row) for row in records(resale["comparables"])),
            int(str(resale["before"])),
            int(str(resale["after"])),
            datetime.fromisoformat(str(resale["valid_until"])) if resale["valid_until"] else None,
        ),
        NewReference(
            str(new["state"]),
            quote,
            str(new["diagnostic"]) if new["diagnostic"] else None,
            int(str(new["failures"])),
        ),
        str(raw["method"]),
    )
