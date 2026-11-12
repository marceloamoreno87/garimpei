from datetime import datetime
from decimal import Decimal
from typing import Literal, NotRequired, TypedDict

from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.listing import Candidate, Evidence, InterestKind, Match


class PointRecord(TypedDict):
    latitude: float
    longitude: float
    accuracy_m: float | None
    city: str
    state: str
    coordinates_known: NotRequired[bool]


class EvidenceRecord(TypedDict):
    published_at_source: NotRequired[str | None]
    image_url: NotRequired[str | None]
    title: str | None
    description: str | None
    condition: str | None
    published_at: str | None
    price: str | None
    freight: str | None
    freight_cep: str | None
    pickup: bool | None
    location: PointRecord | None
    delivery: bool | None
    delivery_cep: str | None
    shipping_offered: NotRequired[bool | None]
    shipping_evidence: NotRequired[str | None]
    pickup_scope_verified: NotRequired[bool | None]
    source_available: NotRequired[bool | None]
    availability_evidence: NotRequired[str | None]


class MatchRecord(TypedDict):
    kind: InterestKind
    key: str


class CandidateRecord(TypedDict):
    external_id: str
    evidence: EvidenceRecord
    origin: Literal["card", "detail"]
    matches: list[MatchRecord]


def encode_evidence(evidence: Evidence) -> EvidenceRecord:
    point = evidence.location
    return {
        "image_url": evidence.image_url,
        "published_at_source": evidence.published_at_source,
        "title": evidence.title,
        "description": evidence.description,
        "condition": evidence.condition,
        "published_at": evidence.published_at.isoformat() if evidence.published_at else None,
        "price": str(evidence.price) if evidence.price is not None else None,
        "freight": str(evidence.freight) if evidence.freight is not None else None,
        "freight_cep": evidence.freight_cep,
        "pickup": evidence.pickup,
        "location": {
            "latitude": point.latitude,
            "longitude": point.longitude,
            "accuracy_m": point.accuracy_m,
            "city": point.city,
            "state": point.state,
            "coordinates_known": point.coordinates_known,
        }
        if point is not None
        else None,
        "delivery": evidence.delivery,
        "delivery_cep": evidence.delivery_cep,
        "shipping_offered": evidence.shipping_offered,
        "shipping_evidence": evidence.shipping_evidence,
        "pickup_scope_verified": evidence.pickup_scope_verified,
        "source_available": evidence.source_available,
        "availability_evidence": evidence.availability_evidence,
    }


def decode_evidence(raw: EvidenceRecord) -> Evidence:
    return Evidence(
        image_url=raw.get("image_url"),
        published_at_source=raw.get("published_at_source"),
        title=raw["title"],
        description=raw["description"],
        condition=raw["condition"],
        published_at=datetime.fromisoformat(raw["published_at"]) if raw["published_at"] else None,
        price=Decimal(raw["price"]) if raw["price"] is not None else None,
        freight=Decimal(raw["freight"]) if raw["freight"] is not None else None,
        freight_cep=raw["freight_cep"],
        pickup=raw["pickup"],
        location=_decode_point(raw["location"]),
        delivery=raw["delivery"],
        delivery_cep=raw["delivery_cep"],
        shipping_offered=raw.get("shipping_offered"),
        shipping_evidence=raw.get("shipping_evidence"),
        pickup_scope_verified=raw.get("pickup_scope_verified"),
        source_available=raw.get("source_available"),
        availability_evidence=raw.get("availability_evidence"),
    )


def encode_candidate(candidate: Candidate) -> CandidateRecord:
    return {
        "external_id": candidate.external_id,
        "evidence": encode_evidence(candidate.evidence),
        "origin": candidate.origin,
        "matches": [{"kind": match.kind, "key": match.key} for match in candidate.matches],
    }


def decode_candidate(data: CandidateRecord) -> Candidate:
    return Candidate(
        data["external_id"],
        decode_evidence(data["evidence"]),
        data["origin"],
        tuple(Match(**match) for match in data["matches"]),
    )


def _decode_point(raw: PointRecord | None) -> Point | None:
    if raw is None:
        return None
    # Before coordinates_known existed, city-only locations used the 0,0 sentinel.
    known = raw.get(
        "coordinates_known",
        not (raw["latitude"] == raw["longitude"] == 0 and raw["accuracy_m"] is None),
    )
    return Point(
        raw["latitude"], raw["longitude"], raw["accuracy_m"], raw["city"], raw["state"], known
    )
