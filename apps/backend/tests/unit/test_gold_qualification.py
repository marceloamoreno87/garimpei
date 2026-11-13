"""Gold qualification cannot be inferred from positive text or manual condition alone."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from garimpei.domain.alert.financial_snapshot import FinancialSnapshot
from garimpei.domain.alert.gold_evidence import GoldEvidence
from garimpei.domain.alert.gold_qualification import qualify
from garimpei.domain.listing.assessment import Assessment
from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identification import identify_product
from garimpei.domain.valuation.values import Comparable, NewReference, Resale, Valuation

NOW = datetime(2026, 11, 13, 12, tzinfo=UTC)


def evidence() -> GoldEvidence:
    listing, observation, evaluation, configuration = (uuid4() for _ in range(4))
    text = Evidence(title="PlayStation 5 Slim disco 1TB", description="Funciona perfeitamente.")
    identity = identify_product(text, observation, 1)
    comparables = tuple(
        Comparable(
            uuid4(),
            "facebook",
            str(index),
            text.title or "",
            "https://example.test/" + str(index),
            Decimal(price),
            NOW,
            1,
            text,
            identification=identity,
        )
        for index, price in enumerate(("2800", "2900", "3000", "3100", "3200"))
    )
    valuation = Valuation(
        evaluation,
        listing,
        1,
        1,
        identity.product_key,
        NOW,
        Resale(Decimal("3000"), None, comparables, 5, 5, NOW + timedelta(days=14)),
        NewReference("unavailable"),
        identification=identity,
    )
    assessment = Assessment(
        uuid4(),
        observation,
        "a" * 64,
        status="complete",
        reason="sufficient_evidence",
        condition="good",
        sufficient=True,
        photo_coverage=({"id": "photo-1", "sha256": "b" * 64, "examined": True},),
    )
    financial = FinancialSnapshot(
        listing,
        None,
        observation,
        evaluation,
        1,
        configuration,
        1,
        Decimal("1900"),
        Decimal("3000"),
        Decimal("10"),
        Decimal("300"),
        Decimal("800"),
        "profit-v3",
        NOW,
        schema_version=2,
    )
    return GoldEvidence(
        listing, observation, 1, text, "good", assessment, identity, valuation, financial, "f" * 64
    )


def test_complete_conjunction_qualifies() -> None:
    value = qualify(evidence(), NOW)
    assert value.state == "qualified"
    assert value.reasons == ("gold_qualified",)
    assert value.canonical_name == "PlayStation 5 Slim com leitor 1 TB"


@pytest.mark.parametrize(
    "condition,expected",
    [("defect", "gold_condition_defect"), ("uncertain", "gold_condition_insufficient")],
)
def test_manual_good_cannot_override_automatic_defect(condition: str, expected: str) -> None:
    value = evidence()
    assert value.financial is not None and value.valuation is not None
    result = qualify(replace(value, assessment=replace(value.assessment, condition=condition)), NOW)
    assert expected in result.reasons
    assert result.state != "qualified"


def test_pending_analysis_and_missing_photos_block() -> None:
    value = evidence()
    assert value.financial is not None and value.valuation is not None
    result = qualify(
        replace(value, assessment=Assessment(observation_id=value.observation_id)), NOW
    )
    assert "gold_condition_pending" in result.reasons
    assert "gold_photos_missing" in result.reasons


def test_positive_text_without_visual_evidence_is_insufficient() -> None:
    value = evidence()
    assert value.financial is not None and value.valuation is not None
    result = qualify(replace(value, assessment=replace(value.assessment, photo_coverage=())), NOW)
    assert result.state == "waiting"
    assert "gold_photos_missing" in result.reasons


@pytest.mark.parametrize("profit", [Decimal("0.00"), Decimal("-100.00")])
def test_non_positive_profit_does_not_qualify(profit: Decimal) -> None:
    value = evidence()
    assert value.financial is not None and value.valuation is not None
    result = qualify(
        replace(
            value,
            financial=replace(value.financial, purchase=Decimal("2700") - profit, profit=profit),
        ),
        NOW,
    )
    assert result.reasons == ("gold_profit_non_positive",)
    assert result.state == "blocked"


def test_one_cent_profit_has_no_additional_threshold() -> None:
    value = evidence()
    assert value.financial is not None and value.valuation is not None
    result = qualify(
        replace(
            value,
            financial=replace(value.financial, purchase=Decimal("2699.99"), profit=Decimal(".01")),
        ),
        NOW,
    )
    assert result.state == "qualified"


def test_validity_is_rechecked_without_input_change() -> None:
    value = evidence()
    assert qualify(value, NOW + timedelta(days=14)).state == "qualified"
    assert (
        "gold_history_expired" in qualify(value, NOW + timedelta(days=14, microseconds=1)).reasons
    )


def test_stale_observation_or_other_variant_blocks() -> None:
    value = evidence()
    assert value.valuation is not None
    assert (
        "gold_evidence_changed"
        in qualify(
            replace(value, assessment=replace(value.assessment, observation_id=uuid4())), NOW
        ).reasons
    )
    assert (
        "gold_identity_conflict"
        in qualify(
            replace(value, valuation=replace(value.valuation, product="sony:ps5:pro:disc:2tb")), NOW
        ).reasons
    )


def test_specific_missing_attribute_reason() -> None:
    value = evidence()
    identity = identify_product(Evidence(title="PS5"), value.observation_id, 1)
    assert (
        "gold_identity_missing_attribute" in qualify(replace(value, identity=identity), NOW).reasons
    )


def test_dependency_failure_never_falls_back() -> None:
    value = evidence()
    assert value.financial is not None and value.valuation is not None
    result = qualify(replace(value, dependency_unavailable=True), NOW)
    assert result.reasons[0] == "gold_dependency_unavailable"
    assert result.state == "waiting"
