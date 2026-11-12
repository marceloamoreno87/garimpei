"""BRL profit policy shared by current listings and immutable event observations."""

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.read_models import Observation
from garimpei.domain.listing.scope import Modality
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.offer_quality import ambiguous_purchase
from garimpei.domain.valuation.values import Valuation

PROFIT_POLICY = "potential-before-freight-v2"
EXCLUDED_COSTS = (
    "purchase_freight",
    "transport",
    "repair",
    "packaging",
    "taxes",
    "resale_shipping",
)


@dataclass(frozen=True)
class Component:
    value: Decimal | None
    state: str
    origin: str | None
    reason: str | None = None


@dataclass(frozen=True)
class ModalityProfit:
    modality: Modality
    freight: Component
    profit: Component
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ProfitInput:
    listing_id: UUID
    observation: Observation
    coverage: Coverage
    applicable_freight: Decimal | None
    configuration: MonitoringSnapshot
    valuation: Valuation | None
    event_id: UUID | None = None


@dataclass(frozen=True)
class ProfitComposition:
    listing_id: UUID
    observation_id: UUID
    event_id: UUID | None
    configuration_id: UUID | None
    configuration_revision: int | None
    evaluation_id: UUID | None
    evaluation_revision: int | None
    calculated_at: datetime
    purchase: Component
    resale: Component
    fee_percent: Decimal | None
    fee: Component
    shipping_freight: Component
    principal: Modality | None
    modalities: tuple[ModalityProfit, ...]
    reasons: tuple[str, ...]
    currency: str = "BRL"
    policy: str = PROFIT_POLICY
    resale_scope: str = "functional_equivalent_without_repair_cost"
    excluded_costs: tuple[str, ...] = EXCLUDED_COSTS

    @property
    def profit(self) -> Component:
        if self.modalities:
            return self.modalities[0].profit
        return Component(None, "indisponivel", None, "modalidade_indisponivel")

    @property
    def freight(self) -> Component:
        if self.modalities:
            return self.modalities[0].freight
        return self.shipping_freight


def _component(value: Decimal | None, state: str, origin: str, reason: str) -> Component:
    return Component(
        value,
        state if value is not None else "indisponivel",
        origin,
        None if value is not None else reason,
    )


def _resale(value: ProfitInput, now: datetime) -> Component:
    valuation = value.valuation
    if ambiguous_purchase(value.observation.evidence):
        return Component(None, "indisponivel", "observation", "preco_parcial_ou_troca")
    if valuation is None:
        return Component(None, "indisponivel", "valuation", "aguardando_avaliacao")
    product = identify(value.observation.evidence)
    if product is None or product != valuation.product or valuation.listing_id != value.listing_id:
        return Component(None, "indisponivel", "valuation", "produto_incompativel")
    if valuation.resale.valid_until is not None and now > valuation.resale.valid_until:
        return Component(None, "indisponivel", "valuation", "evidencia_vencida")
    return _component(
        valuation.resale.price,
        "estimado",
        "valuation",
        valuation.resale.reason or "aguardando_avaliacao",
    )


def _potential(purchase: Component, resale: Component, fee: Component) -> ModalityProfit:
    freight = Component(None, "nao_incluido", None)
    reasons = tuple(item.reason for item in (purchase, resale, fee) if item.reason is not None)
    if reasons:
        return ModalityProfit(
            "marketplace",
            freight,
            Component(None, "indisponivel", None, "componentes_indisponiveis"),
            reasons,
        )
    assert purchase.value is not None and resale.value is not None and fee.value is not None
    amount = resale.value - purchase.value - fee.value
    return ModalityProfit("marketplace", freight, Component(amount, "estimado", PROFIT_POLICY), ())


def compose_profit(value: ProfitInput, now: datetime) -> ProfitComposition:
    config, valuation = value.configuration, value.valuation
    price_origin = dict(value.observation.provenance).get("price", "unknown")
    purchase = _component(
        value.observation.evidence.price,
        "conhecido",
        "observation:" + price_origin,
        "compra_indisponivel",
    )
    resale = _resale(value, now)
    percent = config.resale_fee_percent if config.configured else None
    amount = (
        None
        if resale.value is None or percent is None
        else (resale.value * percent / 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
    )
    fee = _component(
        amount,
        "estimado",
        "configuration",
        "taxa_nao_configurada" if percent is None else "revenda_indisponivel",
    )
    modalities = (_potential(purchase, resale, fee),)
    reasons = modalities[0].reasons
    return ProfitComposition(
        value.listing_id,
        value.observation.id,
        value.event_id,
        config.configuration_id if config.configured else None,
        config.revision if config.configured else None,
        valuation.id if valuation else None,
        valuation.revision if valuation else None,
        now,
        purchase,
        resale,
        percent,
        fee,
        Component(None, "nao_incluido", None),
        "marketplace",
        modalities,
        reasons,
    )
