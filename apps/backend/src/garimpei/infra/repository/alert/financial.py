from garimpei.domain.alert.eligibility import pricing_decision
from garimpei.domain.valuation.profit import ProfitComposition
from garimpei.infra.persistence.listing_models import ListingEvent


def financial_snapshot(
    event: ListingEvent, profit: ProfitComposition | None
) -> tuple[str, str, dict[str, object]]:
    if profit is None:
        return "waiting", "profit_pending", {}
    if (
        profit.event_id != event.id
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
    return (
        "eligible",
        "eligible",
        {
            "event_id": str(event.id),
            "observation_id": str(profit.observation_id),
            "purchase": str(profit.purchase.value),
            "profit": str(profit.profit.value),
            "evaluation_id": str(profit.evaluation_id),
            "evaluation_revision": profit.evaluation_revision,
            "configuration_revision": profit.configuration_revision,
            "principal": profit.principal,
            "policy": profit.policy,
            "excluded_costs": profit.excluded_costs,
            "calculated_at": profit.calculated_at.isoformat(),
        },
    )
