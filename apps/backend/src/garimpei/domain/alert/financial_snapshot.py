"""Validated immutable composition for one observation and its alert origin."""

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

FORMAT = "financial-trio-v1"


@dataclass(frozen=True)
class FinancialSnapshot:
    listing_id: UUID
    event_id: UUID | None
    observation_id: UUID
    evaluation_id: UUID
    evaluation_revision: int
    configuration_id: UUID
    configuration_revision: int
    purchase: Decimal
    resale: Decimal
    fee_percent: Decimal
    fee: Decimal
    profit: Decimal
    policy: str
    calculated_at: datetime
    currency: str = "BRL"
    schema_version: int = 1

    def __post_init__(self) -> None:
        if (
            self.schema_version not in {1, 2}
            or (self.schema_version == 1 and self.event_id is None)
            or (self.schema_version == 2 and self.event_id is not None)
        ):
            raise ValueError(
                "schema_version: expected event snapshot v1 or first eligibility snapshot v2"
            )
        money = (self.purchase, self.resale, self.fee, self.profit)
        if not all(v.is_finite() and v == v.quantize(Decimal(".01")) for v in money):
            raise ValueError("financial: expected finite BRL amounts with at most two decimals")
        if not self.fee_percent.is_finite() or not 0 <= self.fee_percent <= 100:
            raise ValueError("fee_percent: expected finite percentage 0..100")
        expected_fee = (self.resale * self.fee_percent / 100).quantize(
            Decimal(".01"), rounding=ROUND_HALF_UP
        )
        if self.fee != expected_fee or self.profit != self.resale - self.purchase - self.fee:
            raise ValueError("financial: expected a consistent complete composition")
        if self.currency != "BRL" or min(self.purchase, self.resale, self.fee) < 0:
            raise ValueError("financial: expected BRL and nonnegative purchase, resale and fee")
        if self.evaluation_revision < 1 or self.configuration_revision < 1 or not self.policy:
            raise ValueError("financial: expected positive revisions and calculation policy")
        if self.calculated_at.tzinfo is None:
            raise ValueError("calculated_at: expected timezone-aware timestamp")
