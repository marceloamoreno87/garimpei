from decimal import Decimal
from math import degrees
from uuid import uuid4

from garimpei.domain.listing.coverage import coverage
from garimpei.domain.listing.geography import Point
from garimpei.domain.listing.interest_match import matches_product
from garimpei.domain.listing.listing import Evidence, money, price_change
from garimpei.domain.listing.scope import Scope
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.infra.gateway.listing.identity import marketplace_id


def test_identity_tokens_and_money() -> None:
    assert marketplace_id("https://www.facebook.com/marketplace/item/42/?ref=search") == "42"
    assert marketplace_id("https://www.facebook.com.evil.test/marketplace/item/42/") is None
    assert marketplace_id("http://facebook.com/marketplace/item/42/") is None
    assert matches_product("PLＡYSTÁTION 5", "Sony PlayStation 5 Slim")
    assert not matches_product("PlayStation 5", "Sony PlayStation 50")
    assert not matches_product("PlayStation 5", "PlayStation Sony 5")
    assert money("R$ 2.300,00") == Decimal("2300.00")
    assert money("R$ 0") == Decimal("0")
    for label in ("2300", "US$ 2300", "R$ 2300 a R$ 2500", "A combinar", None):
        assert money(label) is None


def test_pickup_boundary_and_precision() -> None:
    origin = Point(-23.55, -46.63, 0, "São Paulo", "SP")
    for distance, error, city, expected in [
        (19.9, 0, "São Paulo", "confirmed"),
        (20, 0, "São Paulo", "confirmed"),
        (20.1, 0, "São Paulo", "excluded"),
        (5, 0, "Osasco", "excluded"),
        (19.9, 200, "São Paulo", "unknown"),
        (5, None, "São Paulo", "unknown"),
        (19.9, None, "São Paulo", "unknown"),
        (20, None, "São Paulo", "unknown"),
        (20.1, None, "São Paulo", "excluded"),
    ]:
        point = Point(origin.latitude + degrees(distance / 6371.0088), -46.63, error, city, "SP")
        result = coverage(origin, "01001000", Evidence(pickup=True, location=point))
        assert result.pickup == expected
        if error is None:
            assert result.pickup_candidate == (distance <= 20)
            assert result.distance_km is not None


def test_delivery_and_freight_are_destination_scoped() -> None:
    for destination, delivery, expected in [
        ("01001000", True, "confirmed"),
        ("01001000", False, "excluded"),
        ("01001001", True, "unknown"),
        (None, None, "unknown"),
    ]:
        result = coverage(None, "01001000", Evidence(delivery_cep=destination, delivery=delivery))
        assert result.shipping == expected
    assert price_change(Decimal("2300"), Decimal("2200")) == "price_decreased"
    assert price_change(Decimal("2200"), Decimal("2400")) == "price_increased"
    assert price_change(Decimal("2200"), Decimal("2200")) is None
    assert price_change(Decimal("2200"), None) is None
    assert price_change(None, Decimal("2200")) is None


def test_scope_keys_fit_persistence_after_unicode_expansion() -> None:
    name = "\ufdfa" * 120
    snapshot = MonitoringSnapshot(
        configured=True,
        configuration_id=uuid4(),
        revision=1,
        cep="01001000",
        product_names=(name,),
    )
    scope = Scope.from_snapshot(snapshot)
    assert scope is not None
    search = scope.searches[0]
    assert len(search.interest.key) <= 400 and len(search.key) <= 450
    assert search.term == name
    assert Scope.from_snapshot(snapshot) == scope


def test_approximate_pickup_and_announced_shipping_remain_qualified_candidates() -> None:
    origin = Point(-23.55, -46.63, None, "São Paulo", "SP")
    point = Point(-23.56, -46.63, None, "São Paulo", "SP")
    observed = coverage(
        origin,
        "01001000",
        Evidence(
            pickup=True,
            location=point,
            shipping_offered=True,
            shipping_evidence="source_delivery_types",
        ),
    )
    assert observed.pickup_candidate and observed.pickup_precision == "approximate"
    assert observed.distance_km is not None and observed.pickup_label == "localização aproximada"
    assert observed.shipping_candidate and observed.shipping == "unknown"
    assert observed.shipping_label == "entrega no CEP a confirmar"
    city_only = coverage(
        origin,
        "01001000",
        Evidence(
            pickup=True,
            pickup_scope_verified=True,
            location=Point(0, 0, None, "São Paulo", "SP", coordinates_known=False),
        ),
    )
    assert city_only.pickup_candidate and city_only.distance_km is None


def test_verified_pickup_query_survives_union_with_shipping_query() -> None:
    from dataclasses import replace

    from garimpei.domain.listing.consolidation import consolidate
    from garimpei.domain.listing.listing import Candidate, Evidence, Match
    from garimpei.domain.listing.scope import Scope
    from garimpei.domain.monitoring.snapshot import MonitoringSnapshot

    scope = Scope.from_snapshot(
        MonitoringSnapshot(
            configured=True,
            configuration_id=uuid4(),
            revision=1,
            cep="01001000",
            product_names=("PlayStation 5",),
        )
    )
    assert scope is not None
    evidence = Evidence(title="PlayStation 5", pickup_scope_verified=True)
    match = Match("product", "playstation 5")
    result = consolidate(
        [
            Candidate("101", evidence, "card", (match,)),
            Candidate("101", replace(evidence, pickup_scope_verified=False), "card", (match,)),
        ],
        scope,
    )
    assert result.evidence.pickup_scope_verified is True
    assert not result.conflicts
