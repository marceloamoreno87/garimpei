from decimal import Decimal

import pytest

from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.errors import ConfigurationConflict, MonitoringError
from garimpei.domain.monitoring.values import Interest, normalize_cep, parse_cost


@pytest.mark.parametrize("value", ["01001-000", "01001000", " 01001000 "])
def test_normalizes_cep(value: str) -> None:
    assert normalize_cep(value) == "01001000"


@pytest.mark.parametrize(
    "value", ["", "０１００１０００", "01001 000", "0100100", "010010000", "abcdefgh"]
)
def test_rejects_invalid_cep(value: str) -> None:
    with pytest.raises(MonitoringError, match="CEP"):
        normalize_cep(value)


@pytest.mark.parametrize(
    "value",
    ["", "-1", "+1", "1,005", "1.005", "1e2", "NaN", "Infinity", "1.000,00", "R$25", "10%", "1_00"],
)
@pytest.mark.parametrize("field", ["shipping_estimate", "resale_fee_percent"])
def test_rejects_ambiguous_costs_without_rounding(value: str, field: str) -> None:
    with pytest.raises(MonitoringError):
        parse_cost(value, field)


@pytest.mark.parametrize(
    "value,expected",
    [("0", "0.00"), ("25,50", "25.50"), ("25.50", "25.50"), ("999999.99", "999999.99")],
)
def test_explicit_costs_preserve_precision(value: str, expected: str) -> None:
    assert str(parse_cost(value, "shipping_estimate")) == expected


def test_cost_boundaries() -> None:
    assert parse_cost("100", "resale_fee_percent") == Decimal("100.00")
    for value, field in [("100.01", "resale_fee_percent"), ("1000000", "shipping_estimate")]:
        with pytest.raises(MonitoringError):
            parse_cost(value, field)


def test_draft_has_no_personal_defaults_and_cannot_publish() -> None:
    draft = MonitoringConfiguration.create()
    assert draft.cep is None and draft.shipping_estimate is None
    assert draft.resale_fee_percent is None and draft.completed_at is None
    assert draft.interests == () and draft.next_step == "regiao"
    with pytest.raises(MonitoringError):
        draft.publish(0)


def test_publication_and_edit_preserve_original_identity_and_completion() -> None:
    draft = MonitoringConfiguration.create().save_region("01001-000", 0)
    draft = draft.save_costs("0", "0", 1)
    draft = draft.save_interests((Interest.product(" PlayStation   5 "),), 2)
    active = draft.publish(3)
    updated = active.update("02002000", "10.25", "100", (Interest.product("Notebook"),), 1)
    assert updated.id == draft.id and updated.completed_at == active.completed_at
    assert updated.revision == 2 and updated.shipping_estimate == Decimal("10.25")
    assert active.shipping_estimate == Decimal("0.00")
    assert active.update("01001000", "0", "0", active.interests, 0) == active
    with pytest.raises(ConfigurationConflict):
        updated.update("03003000", "0", "0", updated.interests, 1)
    with pytest.raises(MonitoringError):
        updated.update("03003000", "0", "0", (), 2)


def test_product_normalization_preserves_display_and_rejects_empty() -> None:
    draft = MonitoringConfiguration.create()
    products = tuple(
        Interest.product(x)
        for x in ["PlayStation 5", " playstation   5 ", "PLAYSTATION 5", "Café", "Cafe\u0301"]
    )
    saved = draft.save_interests(products, 0)
    assert len(saved.interests) == 2
    assert {item.label for item in saved.interests} == {"PlayStation 5", "Café"}
    for value in ["", "   ", "a" * 121]:
        with pytest.raises(MonitoringError):
            Interest.product(value)
    assert Interest.product("<script>alert(1)</script>").label.startswith("<script>")
