from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from garimpei.domain.listing.coverage import Coverage
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.listing.read_models import Observation
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.valuation.profit import ProfitInput, compose_profit
from garimpei.domain.valuation.values import NewReference, Resale, Valuation

NOW = datetime(2026, 11, 10, 18, tzinfo=UTC)


def inputs(*, applicable_freight: Decimal | None = Decimal("40")) -> ProfitInput:
    identity = uuid4()
    observation = Observation(
        uuid4(),
        NOW,
        4,
        "scope",
        Evidence(title="PlayStation 5 Slim Digital 825GB", price=Decimal("1500")),
        Coverage("excluded", "confirmed", None, "none", "destination_verified"),
        (("price", "detail"),),
        (),
    )
    value = ProfitInput(
        identity,
        observation,
        observation.coverage,
        applicable_freight,
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=4,
            resale_fee_percent=Decimal("12.50"),
            shipping_estimate=Decimal("25.50"),
        ),
        Valuation(
            uuid4(),
            identity,
            2,
            4,
            "sony:ps5:slim:digital:825gb",
            NOW,
            Resale(Decimal("2300"), None, (), 5, 5, NOW + timedelta(days=1)),
            NewReference("sem_referencia"),
        ),
    )
    return value


def test_public_composition_closes_and_preserves_sources() -> None:
    value = inputs()
    assert value.valuation is not None
    result = compose_profit(value, NOW)
    assert result.purchase.value == Decimal("1500")
    assert result.purchase.state == "conhecido" and result.purchase.origin == "observation:detail"
    assert result.resale.value == Decimal("2300") and result.resale.state == "estimado"
    assert result.fee.value == Decimal("287.50") and result.fee_percent == Decimal("12.50")
    assert result.freight.value is None and result.freight.state == "nao_incluido"
    assert result.profit.value == Decimal("512.50")
    assert result.observation_id == value.observation.id
    assert result.evaluation_id == value.valuation.id
    assert result.configuration_revision == 4 and result.evaluation_revision == 2
    assert result.currency == "BRL" and result.calculated_at == NOW


@pytest.mark.parametrize(
    "purchase,fee,freight,expected",
    [
        ("1500", "0", "0", "800.00"),
        ("0", "100", "0", "0.00"),
        ("0", "0", "0", "2300.00"),
        ("2012.50", "12.50", "25.50", "0.00"),
        ("2030", "12.50", "25.50", "-17.50"),
    ],
)
def test_decimal_limits_and_known_zero(
    purchase: str, fee: str, freight: str, expected: str
) -> None:
    value = inputs(applicable_freight=Decimal(freight))
    value = replace(
        value,
        observation=replace(
            value.observation, evidence=replace(value.observation.evidence, price=Decimal(purchase))
        ),
        configuration=replace(value.configuration, resale_fee_percent=Decimal(fee)),
    )
    assert compose_profit(value, NOW).profit.value == Decimal(expected)


def test_half_cent_and_logistics_independent_potential() -> None:
    value = inputs()
    assert value.valuation is not None
    value = replace(
        value,
        coverage=replace(value.coverage, pickup="confirmed"),
        observation=replace(
            value.observation, evidence=replace(value.observation.evidence, price=Decimal("70"))
        ),
        valuation=replace(
            value.valuation, resale=replace(value.valuation.resale, price=Decimal("101"))
        ),
    )
    result = compose_profit(value, NOW)
    assert result.fee.value == Decimal("12.63")
    assert result.principal == "marketplace" and result.freight.state == "nao_incluido"
    assert result.freight.value is None and result.profit.value == Decimal("18.37")
    assert len(result.modalities) == 1


@pytest.mark.parametrize("reason", ["amostra_insuficiente", "evidencia_vencida"])
def test_unavailable_resale_keeps_other_inputs(reason: str) -> None:
    value = inputs()
    assert value.valuation is not None
    value = replace(
        value,
        valuation=replace(
            value.valuation, resale=replace(value.valuation.resale, price=None, reason=reason)
        ),
    )
    result = compose_profit(value, NOW)
    assert result.resale.value is None and result.resale.reason == reason
    assert result.profit.value is None and result.fee.value is None
    assert result.purchase.value == Decimal("1500") and result.freight.value is None
    assert result.fee_percent == Decimal("12.50")


def test_missing_configuration_purchase_modality_and_expired_or_wrong_valuation() -> None:
    value = inputs()
    assert value.valuation is not None
    draft = compose_profit(replace(value, configuration=MonitoringSnapshot()), NOW)
    assert draft.configuration_revision is None and draft.fee_percent is None
    assert draft.fee.value is None and draft.profit.value is None
    assert draft.purchase.value == Decimal("1500") and draft.resale.value == Decimal("2300")
    unknown = compose_profit(
        replace(value, coverage=replace(value.coverage, shipping="unknown")), NOW
    )
    assert unknown.principal == "marketplace" and unknown.profit.value == Decimal("512.50")
    assert unknown.reasons == ()
    assert unknown.freight.value is None
    missing = compose_profit(
        replace(
            value,
            observation=replace(
                value.observation, evidence=replace(value.observation.evidence, price=None)
            ),
        ),
        NOW,
    )
    assert missing.profit.value is None and missing.fee.value == Decimal("287.50")
    for valuation in (
        None,
        replace(value.valuation, product="other"),
        replace(
            value.valuation,
            resale=replace(value.valuation.resale, valid_until=NOW - timedelta(seconds=1)),
        ),
    ):
        result = compose_profit(replace(value, valuation=valuation), NOW)
        assert result.resale.value is None and result.profit.value is None


def test_missing_required_freight_and_pending_valuation_preserve_known_parts() -> None:
    value = inputs(applicable_freight=None)
    assert value.valuation is not None
    absent = compose_profit(
        replace(value, configuration=replace(value.configuration, shipping_estimate=None)), NOW
    )
    assert absent.profit.value == Decimal("512.50") and absent.freight.value is None
    assert "frete_indisponivel" not in absent.reasons
    assert absent.purchase.value == Decimal("1500") and absent.fee.value == Decimal("287.50")
    pending = compose_profit(
        replace(
            value,
            valuation=replace(
                value.valuation,
                id=None,
                resale=replace(value.valuation.resale, price=None, reason="aguardando_avaliacao"),
            ),
        ),
        NOW,
    )
    assert pending.resale.reason == "aguardando_avaliacao" and pending.evaluation_id is None
    assert pending.purchase.value == Decimal("1500") and pending.freight.value is None
    assert pending.profit.value is None
