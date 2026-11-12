from datetime import datetime
from decimal import InvalidOperation

from garimpei.domain.alert.financial_snapshot import FinancialSnapshot
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.profit import ProfitComposition
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
from garimpei.infra.persistence.valuation_models import ValuationProgress
from garimpei.infra.repository.alert.financial import encode_snapshot
from garimpei.infra.repository.listing.mapper import decode_evidence
from garimpei.infra.repository.valuation.mapper import decode_valuation, mapping


def first_snapshot(
    listing: Listing, profit: ProfitComposition | None
) -> tuple[str, dict[str, object]]:
    if listing.latest is None:
        return "profit_pending", {}
    if profit is None:
        return "profit_pending", {}
    if (
        profit.listing_id != listing.id
        or profit.observation_id != listing.latest_id
        or profit.event_id is not None
        or profit.purchase.value != listing.latest.price
    ):
        return "profit_observation_mismatch", {}
    if (
        profit.profit.value is None
        and "produto_incompativel" in profit.reasons
        and identify(decode_evidence(listing.latest.evidence)) is None
    ):
        return "produto_indeterminado", {}
    if profit.profit.value is None:
        return next(iter(profit.reasons), "profit_pending"), {}
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
        return "profit_incomplete", {}
    try:
        value = FinancialSnapshot(
            profit.listing_id,
            None,
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
            schema_version=2,
        )
    except (ValueError, InvalidOperation):
        return "profit_incompatible", {}
    if not first_references(value, profit.calculated_at):
        return "profit_stale", {}
    return "eligible", encode_snapshot(value)


def first_references(value: FinancialSnapshot, now: datetime) -> bool:
    if not MonitoringConfiguration.objects.filter(
        id=value.configuration_id, slot="active", revision=value.configuration_revision
    ).exists():
        return False
    progress = (
        ValuationProgress.objects.select_related("current")
        .filter(listing_id=value.listing_id, current_id=value.evaluation_id)
        .first()
    )
    if progress is None or progress.current is None:
        return False
    valuation = decode_valuation(mapping(progress.current.result))
    return bool(
        valuation.id == value.evaluation_id
        and valuation.revision == value.evaluation_revision
        and valuation.resale.price == value.resale
        and valuation.resale.valid_until is not None
        and now <= valuation.resale.valid_until
    )
