from collections.abc import Callable
from dataclasses import dataclass

from garimpei.domain.listing.listing import Candidate, Evidence, Match
from garimpei.domain.listing.scope import Scope


@dataclass(frozen=True)
class Consolidated:
    external_id: str
    evidence: Evidence
    matches: tuple[Match, ...]
    provenance: tuple[tuple[str, str], ...]
    conflicts: tuple[str, ...]


def consolidate(candidates: list[Candidate], scope: Scope) -> Consolidated:
    provenance: list[tuple[str, str]] = []
    conflicts: list[str] = []

    def select[T](name: str, value: Callable[[Evidence], T | None]) -> T | None:
        for origin in ("detail", "card"):
            entries = {
                observed
                for item in candidates
                if item.origin == origin and (observed := value(item.evidence)) is not None
            }
            if len(entries) == 1:
                provenance.append((name, origin))
                return entries.pop()
            if entries:
                conflicts.append(name)
                return None
        return None

    available = select("source_available", lambda e: e.source_available)
    freight, freight_cep = select(
        "freight", lambda e: (e.freight, e.freight_cep) if e.freight is not None else None
    ) or (None, None)
    delivery, delivery_cep = select(
        "delivery", lambda e: (e.delivery, e.delivery_cep) if e.delivery is not None else None
    ) or (None, None)
    publication = select(
        "publication",
        lambda e: (
            (e.published_at, e.published_at_source)
            if e.published_at is not None or e.published_at_source is not None
            else None
        ),
    )
    evidence = Evidence(
        image_url=select("image_url", lambda e: e.image_url),
        title=select("title", lambda e: e.title),
        description=select("description", lambda e: e.description),
        condition=select("condition", lambda e: e.condition),
        published_at=publication[0] if publication else None,
        published_at_source=publication[1] if publication else None,
        price=select("price", lambda e: e.price) if available is not False else None,
        freight=freight if available is not False else None,
        freight_cep=freight_cep if available is not False else None,
        pickup=select("pickup", lambda e: e.pickup),
        location=select("location", lambda e: e.location),
        delivery=delivery,
        delivery_cep=delivery_cep,
        shipping_offered=select("shipping_offered", lambda e: e.shipping_offered),
        shipping_evidence=select("shipping_evidence", lambda e: e.shipping_evidence),
        pickup_scope_verified=select(
            "pickup_scope_verified", lambda e: True if e.pickup_scope_verified else None
        ),
        source_available=available,
        availability_evidence=select("availability_evidence", lambda e: e.availability_evidence),
    )
    prior = {match for item in candidates for match in item.matches}
    categories = {
        match for item in candidates for match in item.matches if match.kind == "category"
    }
    matches = {
        search.interest
        for search in scope.searches
        if search.interest in categories
        or (evidence.source_available is False and search.interest in prior)
        or (
            search.interest.kind == "product"
            and evidence.title is not None
            and search.matches_title(evidence.title)
        )
    }
    return Consolidated(
        candidates[0].external_id,
        evidence,
        tuple(sorted(matches)),
        tuple(provenance),
        tuple(conflicts),
    )
