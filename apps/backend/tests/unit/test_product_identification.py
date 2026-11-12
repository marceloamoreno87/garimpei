from datetime import UTC, datetime
from uuid import uuid4

import pytest

from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identification import identify_product
from garimpei.domain.valuation.identity_errors import InvalidIdentityCombination
from garimpei.domain.valuation.manual_identity import ManualIdentity

NOW = datetime(2026, 11, 12, 19, tzinfo=UTC)
VALUES = dict(family="playstation5", model="ps5", generation="slim", edition="disc", capacity="1tb")


def test_automatic_attributes_keep_exact_observation_and_literal_evidence() -> None:
    observation = uuid4()
    value = identify_product(Evidence(title="PlayStation 5 Slim disco 1TB"), observation, 3)
    assert value.state == "identified" and value.product_key == "sony:ps5:slim:disc:1tb"
    assert {a.name: a.value for a in value.attributes}["capacity"] == "1tb"
    for attribute in value.attributes:
        assert attribute.origin == "automatic"
        assert attribute.observation_id == observation and attribute.input_revision == 3
        assert attribute.quote is not None
        assert attribute.field == "title" and attribute.quote in "PlayStation 5 Slim disco 1TB"


def test_missing_attribute_is_named_without_forcing_variant_incompatibility() -> None:
    value = identify_product(Evidence(title="PS5 Slim disco funcionando"), uuid4(), 1)
    assert value.state == "missing_attribute" and "capacity" in value.missing_attributes
    assert value.product_key is None and not value.conflicts


def test_unknown_unsupported_and_excluded_inputs_have_distinct_states() -> None:
    for title, expected in [
        ("Objeto sem identificação", "unrecognized"),
        ("Notebook Acer Aspire", "unsupported_family"),
        ("Capa para iPhone 13 128GB", "excluded_item"),
    ]:
        assert identify_product(Evidence(title=title), uuid4(), 1).state == expected


def test_explicit_conflicting_capacity_keeps_the_competing_source_values() -> None:
    value = identify_product(
        Evidence(title="iPhone 13 128GB", description="Modelo de 256GB"), uuid4(), 1
    )
    assert value.state == "conflicting_identity" and value.product_key is None
    assert {c.observed_value for c in value.conflicts} >= {"128gb", "256gb"}


def test_manual_identity_retains_source_independence_and_survives_absence() -> None:
    manual = ManualIdentity.create(VALUES, revision=1, reviewed_revision=3, recorded_at=NOW)
    value = identify_product(Evidence(title="PS5 Slim funcionando"), uuid4(), 4, manual)
    assert value.state == "identified" and value.product_key == "sony:ps5:slim:disc:1tb"
    for attribute in value.attributes:
        assert attribute.origin == "manual" and attribute.quote is None
        assert attribute.recorded_at == NOW and attribute.reviewed_revision == 3


def test_explicit_contradiction_blocks_manual_identity_until_review() -> None:
    manual = ManualIdentity.create(VALUES, revision=1, reviewed_revision=3, recorded_at=NOW)
    source = Evidence(title="PS5 Slim disco 2TB")
    value = identify_product(source, uuid4(), 4, manual)
    assert value.state == "conflicting_identity" and value.product_key is None
    assert any(
        c.name == "capacity" and c.manual_value == "1tb" and c.observed_value == "2tb"
        for c in value.conflicts
    )
    reviewed = manual.review(value.conflicts, reviewed_revision=4, recorded_at=NOW)
    repeated = identify_product(source, uuid4(), 5, reviewed)
    assert repeated.state == "identified" and repeated.product_key == manual.product_key
    new_conflict = identify_product(Evidence(title="PS5 Slim disco 825GB"), uuid4(), 6, reviewed)
    assert new_conflict.state == "conflicting_identity"


def test_missing_iphone_edition_does_not_contradict_an_explicit_manual_pro() -> None:
    manual = ManualIdentity.create(
        dict(family="iphone", model="13", edition="pro", capacity="128gb"),
        revision=1,
        reviewed_revision=1,
        recorded_at=NOW,
    )
    value = identify_product(Evidence(title="iPhone 13 128GB"), uuid4(), 2, manual)
    assert value.state == "identified" and value.product_key == "apple:iphone13:pro:128gb"


@pytest.mark.parametrize(
    "values",
    [
        dict(family="notebook", model="acer"),
        VALUES | {"capacity": "500gb"},
        VALUES | {"secret": "unsupported"},
    ],
)
def test_manual_values_cannot_invent_family_support_or_unknown_attributes(
    values: dict[str, str],
) -> None:
    with pytest.raises(InvalidIdentityCombination):
        ManualIdentity.create(values, revision=1, reviewed_revision=1, recorded_at=NOW)
