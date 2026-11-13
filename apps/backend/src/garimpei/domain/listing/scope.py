import hashlib
import json
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from garimpei.domain.listing.geography import MARKETPLACE_RADIUS_KM, MARKETPLACE_SEARCH_ORIGIN
from garimpei.domain.listing.interest_match import matches_product, tokens
from garimpei.domain.listing.listing import MAX_INTEREST_KEY_LENGTH, Match
from garimpei.domain.listing.window import PublicationWindow
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot

Modality = Literal["pickup", "shipping", "marketplace"]
MODALITIES: tuple[Modality, ...] = ("marketplace",)


@dataclass(frozen=True)
class Search:
    interest: Match
    term: str
    modality: Modality
    equivalent_terms: tuple[str, ...] = ()
    excluded_terms: tuple[str, ...] = ()
    purpose: Literal["active", "research"] = "active"

    def matches_title(self, title: str) -> bool:
        if any(word in tokens(title) for word in self.excluded_terms):
            return False
        return any(matches_product(term, title) for term in (self.term, *self.equivalent_terms))

    @property
    def key(self) -> str:
        return f"{self.modality}:{self.interest.kind}:{self.interest.key}"


@dataclass(frozen=True)
class Scope:
    configuration_id: UUID
    source: str
    cep: str
    revision: int
    key: str
    searches: tuple[Search, ...]
    window: PublicationWindow | None = None

    @classmethod
    def from_snapshot(cls, snapshot: MonitoringSnapshot) -> "Scope | None":
        if (
            not snapshot.configured
            or snapshot.configuration_id is None
            or snapshot.revision is None
            or snapshot.cep is None
        ):
            return None
        interests = {Match("category", category): category for category in snapshot.category_ids}
        for term in snapshot.product_names:
            # Keep a lookup key for punctuation-only names and for Unicode compatibility
            # forms whose normalized expansion exceeds the storage limit.
            key = " ".join(tokens(term)) or term.casefold()
            if len(key) > MAX_INTEREST_KEY_LENGTH:
                key = "sha256:" + hashlib.sha256(key.encode()).hexdigest()
            interests.setdefault(Match("product", key), term)
        searches = tuple(
            Search(interest, interests[interest], modality)
            for interest in sorted(interests)
            for modality in MODALITIES
        )
        identity = [(interest.kind, interest.key) for interest in sorted(interests)]
        key = hashlib.sha256(
            json.dumps(
                [
                    snapshot.source,
                    snapshot.cep,
                    identity,
                    "48h-marketplace-potential-v5-city-source",
                    MARKETPLACE_RADIUS_KM,
                    MARKETPLACE_SEARCH_ORIGIN.latitude,
                    MARKETPLACE_SEARCH_ORIGIN.longitude,
                    MARKETPLACE_SEARCH_ORIGIN.city,
                    MARKETPLACE_SEARCH_ORIGIN.state,
                ]
            ).encode()
        ).hexdigest()
        return cls(
            snapshot.configuration_id,
            snapshot.source,
            snapshot.cep,
            snapshot.revision,
            key,
            searches,
        )
