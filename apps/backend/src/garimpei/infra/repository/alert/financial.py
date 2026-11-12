from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from garimpei.domain.alert.eligibility import pricing_decision
from garimpei.domain.alert.financial_snapshot import FinancialSnapshot
from garimpei.domain.valuation.profit import ProfitComposition
from garimpei.infra.persistence.listing_models import ListingEvent


def encode_snapshot(value: FinancialSnapshot) -> dict[str, object]:
    return {
        "schema_version": value.schema_version,
        "listing_id": str(value.listing_id),
        "event_id": str(value.event_id) if value.event_id else None,
        "observation_id": str(value.observation_id),
        "evaluation_id": str(value.evaluation_id),
        "evaluation_revision": value.evaluation_revision,
        "configuration_id": str(value.configuration_id),
        "configuration_revision": value.configuration_revision,
        "purchase": str(value.purchase),
        "resale": str(value.resale),
        "fee_percent": str(value.fee_percent),
        "fee": str(value.fee),
        "profit": str(value.profit),
        "currency": value.currency,
        "policy": value.policy,
        "calculated_at": value.calculated_at.isoformat(),
    }


def decode_snapshot(raw: dict[str, object]) -> FinancialSnapshot | None:
    try:
        return FinancialSnapshot(
            UUID(str(raw["listing_id"])),
            UUID(str(raw["event_id"])) if raw["event_id"] is not None else None,
            UUID(str(raw["observation_id"])),
            UUID(str(raw["evaluation_id"])),
            int(str(raw["evaluation_revision"])),
            UUID(str(raw["configuration_id"])),
            int(str(raw["configuration_revision"])),
            Decimal(str(raw["purchase"])),
            Decimal(str(raw["resale"])),
            Decimal(str(raw["fee_percent"])),
            Decimal(str(raw["fee"])),
            Decimal(str(raw["profit"])),
            str(raw["policy"]),
            datetime.fromisoformat(str(raw["calculated_at"])),
            str(raw["currency"]),
            schema_version=int(str(raw["schema_version"])),
        )
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return None


def financial_snapshot(
    event: ListingEvent, profit: ProfitComposition | None
) -> tuple[str, str, dict[str, object]]:
    if profit is None:
        return "waiting", "profit_pending", {}
    if (
        profit.listing_id != event.listing_id
        or profit.event_id != event.id
        or profit.observation_id != event.observation_id
        or profit.purchase.value != event.observation.price
    ):
        return "waiting", "profit_observation_mismatch", {}
    if "aguardando_avaliacao" in profit.reasons:
        return "waiting", "profit_pending", {}
    if profit.profit.value is None:
        reason = next(iter(profit.reasons), "profit_unavailable")
        state, reason = pricing_decision(reason, event.occurred_at, profit.calculated_at)
        return state, reason, {}
    if (
        profit.evaluation_id is None
        or profit.configuration_id is None
        or profit.evaluation_revision is None
        or profit.configuration_revision is None
        or profit.purchase.value is None
        or profit.resale.value is None
        or profit.fee_percent is None
        or profit.fee.value is None
    ):
        return "waiting", "profit_incomplete", {}
    try:
        snapshot = FinancialSnapshot(
            profit.listing_id,
            event.id,
            profit.observation_id,
            profit.evaluation_id,
            profit.evaluation_revision,
            profit.configuration_id,
            profit.configuration_revision,
            profit.purchase.value,
            profit.resale.value,
            profit.fee_percent,
            profit.fee.value,
            profit.profit.value,
            profit.policy,
            profit.calculated_at,
            profit.currency,
        )
    except (ValueError, InvalidOperation):
        return "waiting", "profit_incompatible", {}
    return "eligible", "eligible", encode_snapshot(snapshot)
