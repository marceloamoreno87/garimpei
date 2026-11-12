from dataclasses import replace
from uuid import uuid4

from garimpei.domain.listing.condition import ConditionState, automatic_condition
from garimpei.domain.listing.exploration import Criteria, Offer
from garimpei.domain.valuation.profit import compose_profit
from garimpei.infra.http.listing.exploration_presentation import card, detail_context
from tests.unit.test_profit import NOW, inputs


def offer() -> Offer:
    value = inputs()
    return Offer(
        value.listing_id,
        "synthetic",
        "facebook_marketplace",
        "https://example.invalid/item",
        NOW,
        NOW,
        value.observation.evidence,
        ConditionState(automatic_condition(value.observation.evidence)),
        (),
        True,
        False,
        True,
        compose_profit(value, NOW),
        value.valuation,
        observation_id=value.observation.id,
    )


def test_financial_labels_are_estimates_without_logistic_copy() -> None:
    result = card(offer(), Criteria())
    assert result["profit_label"] == "Lucro estimado"
    assert result["resale"] == "R$ 2.300,00"
    assert "frete" not in str(result.get("profit_scope", "")).lower()


def test_incompatible_composition_does_not_mix_other_observation_values() -> None:
    value = offer()
    value = replace(value, composition=replace(value.composition, listing_id=uuid4()))
    result = detail_context(value, Criteria())
    assert result["price"] == "R$ 1.500,00"
    assert result["resale"] == "Indisponível"
    assert result["profit"] == "Indisponível"
    assert result["reason"] == "Composição indisponível para esta revisão"


def test_complete_snapshot_roundtrip_validates_components_and_provenance() -> None:
    from decimal import Decimal

    from garimpei.domain.alert.financial_snapshot import FinancialSnapshot
    from garimpei.infra.repository.alert.financial import decode_snapshot, encode_snapshot

    value = FinancialSnapshot(
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        1,
        uuid4(),
        2,
        Decimal("70"),
        Decimal("101"),
        Decimal("12.50"),
        Decimal("12.63"),
        Decimal("18.37"),
        "potential-before-freight-v2",
        NOW,
    )
    raw = encode_snapshot(value)
    assert decode_snapshot(raw) == value
    first = replace(value, event_id=None, schema_version=2)
    first_raw = encode_snapshot(first)
    assert first_raw["event_id"] is None and decode_snapshot(first_raw) == first
    assert decode_snapshot(first_raw | {"schema_version": 3}) is None
    assert decode_snapshot(raw | {"event_id": None}) is None
    for key, corrupted in [
        ("schema_version", 2),
        ("profit", "18.38"),
        ("fee", "12.62"),
        ("purchase", "NaN"),
        ("resale", "Infinity"),
        ("currency", "USD"),
        ("event_id", "invalid"),
        ("fee_percent", "-1"),
    ]:
        assert decode_snapshot(raw | {key: corrupted}) is None
    for key in raw:
        assert decode_snapshot({k: v for k, v in raw.items() if k != key}) is None


def test_trio_message_uses_complete_frozen_money_with_negative_and_zero() -> None:
    from decimal import Decimal

    from garimpei.domain.alert.alert import AlertMessage
    from garimpei.domain.alert.eligibility import message_text
    from garimpei.domain.alert.financial_snapshot import FinancialSnapshot

    for purchase, profit in [("1000", "350"), ("1350", "0"), ("1400", "-50")]:
        value = FinancialSnapshot(
            uuid4(),
            uuid4(),
            uuid4(),
            uuid4(),
            1,
            uuid4(),
            1,
            Decimal(purchase),
            Decimal("1500"),
            Decimal("10"),
            Decimal("150"),
            Decimal(profit),
            "potential-before-freight-v2",
            NOW,
        )
        message = AlertMessage(
            uuid4(),
            "price_decreased",
            "PS5\nSlim",
            "Facebook Marketplace",
            value.purchase,
            Decimal("1600"),
            value.profit,
            NOW,
            "https://example.invalid/item",
            financial=value,
        )
        body = message_text(message)
        assert (
            body.index("Preço de compra:")
            < body.index("Preço de venda estimado:")
            < body.index("*Lucro estimado:")
        )
        assert "frete" not in body.lower() and "transporte" not in body.lower()
        assert "Preço reduzido" in body and "Preço anterior: R$ 1.600,00" in body
        assert (
            "-R$ 50,00*" if profit == "-50" else "R$ 0,00*" if profit == "0" else "R$ 350,00*"
        ) in body


def test_legacy_publication_retains_its_frozen_composition() -> None:
    from garimpei.infra.queries.listing.exploration_mapper import decode, encode

    value = offer()
    raw = encode(value)
    raw.pop("observation_id")
    restored = decode(raw, NOW)
    result = card(restored, Criteria())
    assert result["resale"] == "R$ 2.300,00"
    assert result["profit"] == "R$ 512,50"


def test_other_evaluation_or_variant_cannot_supply_published_values() -> None:
    value = offer()
    assert value.valuation is not None
    for composition in [
        replace(value.composition, evaluation_id=uuid4()),
        replace(value.composition, evaluation_revision=999),
    ]:
        result = card(replace(value, composition=composition), Criteria())
        assert result["resale"] == "Indisponível"
        assert result["profit"] == "Indisponível"
    other = replace(value.valuation, product="apple:iphone13:standard:128gb")
    assert card(replace(value, valuation=other), Criteria())["resale"] == "Indisponível"


def test_absent_composition_keeps_offer_readable_without_inventing_resale() -> None:
    from garimpei.infra.queries.listing.exploration_mapper import decode, encode

    raw = encode(offer())
    raw.pop("composition")
    restored = decode(raw, NOW)
    result = detail_context(restored, Criteria())
    assert result["price"] == "R$ 1.500,00"
    assert result["resale"] == "Indisponível"
    assert result["profit"] == "Indisponível"
    assert result["reason"] == "Composição indisponível para esta revisão"


def test_missing_required_component_never_renders_a_numeric_profit() -> None:
    from garimpei.domain.valuation.profit import Component

    value = offer()
    missing = Component(None, "indisponivel", None, "not_provided")
    for composition in [
        replace(value.composition, resale=missing),
        replace(value.composition, fee=missing),
        replace(value.composition, fee_percent=None),
    ]:
        result = card(replace(value, composition=composition), Criteria())
        assert result["profit"] == "Estimativa indisponível"
