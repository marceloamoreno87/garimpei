from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from garimpei.domain.alert.alert import AlertMessage, Binding, Receipt
from garimpei.domain.alert.eligibility import eligibility, message_text, verified_receipt


@pytest.mark.parametrize("profit", ["180.00", "0.00", "-12.35"])
def test_eligible_profit_has_no_minimum_and_message_preserves_values(profit: str) -> None:
    assert eligibility("discovered", False, True, True, "good", True, False) == "eligible"
    value = AlertMessage(
        uuid4(),
        "discovered",
        "PS5\nSlim",
        "Facebook Marketplace",
        Decimal("2300"),
        None,
        Decimal(profit),
        datetime(2026, 11, 10, 22, 42, tzinfo=UTC),
        "https://www.facebook.com/marketplace/item/123/",
    )
    text = message_text(value)
    assert "Nova oferta" in text and "PS5 Slim" in text and "R$ 2.300,00" in text
    assert ("-R$ 12,35" if profit.startswith("-") else "R$ " + profit.replace(".", ",")) in text
    assert "19:42" in text and str(value.reference) in text and value.url in text


@pytest.mark.parametrize(
    ("kind", "silent", "covered", "matched", "condition", "reason"),
    [
        ("discovered", True, True, True, "good", "silent"),
        ("price_increased", False, True, True, "good", "unsupported_event"),
        ("discovered", False, False, True, "good", "coverage_unconfirmed"),
        ("discovered", False, True, False, "good", "interest_unconfirmed"),
        ("discovered", False, True, True, "defect", "condition_excluded"),
        ("discovered", False, True, True, "uncertain", "condition_excluded"),
    ],
)
def test_exclusions_are_explicit(
    kind: str, silent: bool, covered: bool, matched: bool, condition: str, reason: str
) -> None:
    assert eligibility(kind, silent, covered, matched, condition, True, False) == reason


def test_reduction_waits_for_previous_attempt_then_requires_confirmation() -> None:
    args = ("price_decreased", False, True, True, "good")
    assert eligibility(*args, False, True) == "waiting_previous"
    assert eligibility(*args, False, False) == "no_previous_confirmation"
    assert eligibility(*args, True, False) == "eligible"


def test_ack_needs_outgoing_body_chat_and_unambiguous_identity() -> None:
    binding = Binding("synthetic", "100@c.us", "200@c.us")
    receipt = Receipt("id", True, "100@c.us", "body", 1)
    assert verified_receipt(receipt, binding, "body")
    for other in [
        Receipt("id", False, "100@c.us", "body", 2),
        Receipt("id", True, "other", "body", 2),
        Receipt("id", True, "100@c.us", "wrong", 2),
        Receipt("id", True, "100@c.us", "body", 0),
    ]:
        assert not verified_receipt(other, binding, "body")
