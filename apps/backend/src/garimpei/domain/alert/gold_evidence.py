"""Immutable evidence consumed by gold policy; producers own prices and condition analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from garimpei.domain.alert.financial_snapshot import FinancialSnapshot
from garimpei.domain.listing.assessment import Assessment
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identification_values import IdentificationResult
from garimpei.domain.valuation.values import Valuation

POLICY = "gold-alert-v1"


@dataclass(frozen=True)
class GoldEvidence:
    listing_id: UUID
    observation_id: UUID
    observation_revision: int
    text: Evidence
    effective_condition: str
    assessment: Assessment
    identity: IdentificationResult
    valuation: Valuation | None
    financial: FinancialSnapshot | None
    fingerprint: str
    dependency_unavailable: bool = False
    applicable: bool = True


@dataclass(frozen=True)
class GoldDecision:
    listing_id: UUID
    observation_id: UUID
    purpose_key: str
    input_fingerprint: str
    state: str
    reasons: tuple[str, ...]
    canonical_name: str
    product_key: str | None
    evaluated_at: datetime
    valid_until: datetime | None
    policy: str = POLICY
    id: UUID | None = None

    @property
    def reason(self) -> str:
        return self.reasons[0]


class GoldEvidenceRepository(Protocol):
    def qualify(self, listing_id: UUID, purpose_key: str, now: datetime) -> GoldDecision: ...


class GoldPolicyRepository(Protocol):
    def adopt(self, now: datetime) -> dict[str, object]: ...
