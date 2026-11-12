from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from garimpei.domain.listing.listing import Evidence
from garimpei.domain.valuation.identity import identify
from garimpei.domain.valuation.policy import eligible, estimate, new_reference
from garimpei.domain.valuation.values import Comparable, NewQuote

NOW = datetime(2026, 11, 10, 18, tzinfo=UTC)
TITLE = "Sony PlayStation 5 Slim Digital 825GB"


def sample(price: str, *, age: timedelta = timedelta(), identity: str = "") -> Comparable:
    return Comparable(
        uuid4(),
        "facebook_marketplace",
        identity or str(uuid4()),
        TITLE,
        "https://exemplo.invalid/item",
        Decimal(price),
        NOW - age,
        1,
        Evidence(
            title=TITLE,
            description="Usado. Funcionando perfeitamente.",
            condition="Usado — seminovo",
            source_available=True,
        ),
    )


def test_estimated_price_uses_five_distinct_functional_equivalents() -> None:
    target = sample("1300")
    candidates = tuple(
        sample(str(p), identity=f"C{i}") for i, p in enumerate(range(2100, 2600, 100))
    )
    from dataclasses import replace

    old_c2 = replace(
        candidates[1], price=Decimal("2150"), observed_at=NOW - timedelta(days=1), revision=0
    )
    result = estimate(target, candidates + (old_c2, target, sample("4200")), NOW)
    assert result.price == Decimal("2300.00")
    assert {c.external_id for c in result.comparables} == {f"C{i}" for i in range(5)}
    assert result.after == 5
    assert result.state == "disponivel"
    assert all(row.price_kind == "announced" for row in result.comparables)


def test_short_dispersed_and_expired_samples_never_invent_prices() -> None:
    target = sample("1300")
    short = tuple(sample(str(p)) for p in [2100, 2200, 2300, 2400, 4200])
    result = estimate(target, short, NOW)
    assert (result.price, result.reason, result.after) == (None, "amostra_insuficiente", 4)
    assert (
        estimate(target, tuple(sample(str(p)) for p in [1500, 1800, 2200, 2500, 2600]), NOW).reason
        == "amostra_dispersa"
    )
    edge = sample("2100", age=timedelta(days=14))
    rest = tuple(sample(str(p)) for p in [2200, 2300, 2400, 2500])
    assert estimate(target, (edge,) + rest, NOW).price == Decimal("2300.00")
    assert estimate(target, (edge,) + rest, NOW + timedelta(seconds=1)).price is None


def test_variant_ambiguity_and_new_reference_independence() -> None:
    key = identify(Evidence(title=TITLE))
    assert key is not None
    assert identify(Evidence(title="PlayStation 5")) is None
    assert identify(Evidence(title="PS5 Slim Digital 825GB CFI-2114A")) is None
    assert identify(Evidence(title=TITLE, description="Troco por iPhone 13 128GB")) is None
    assert identify(Evidence(title="PS5 Slim Digital 1TB")) != key
    quote = NewQuote(key, "kabum", "N", "Novo", "https://exemplo.invalid/new", Decimal("3800"), NOW)
    assert new_reference(key, (quote,), False, None, NOW).quote == quote
    assert new_reference(key, (), False, None, NOW).state == "sem_referencia"
    assert new_reference(key, (), True, quote, NOW + timedelta(days=7)).quote == quote
    assert (
        new_reference(key, (), True, quote, NOW + timedelta(days=7, seconds=1)).state
        == "fonte_indisponivel"
    )


def test_real_market_sample_reproduces_phase_one_value() -> None:
    import json
    from dataclasses import replace
    from pathlib import Path
    from uuid import UUID

    folder = (
        Path(__file__).resolve().parents[4]
        / "docs/F06-referencias-de-precos-e-estimativa-de-revenda/evidence/2026-11-11T17-07-37Z"
    )
    rows = json.loads((folder / "used-probe.json").read_text())["observations"]
    candidates = []
    for row in rows:
        if "evidence" not in row:
            continue
        e = row["evidence"]
        evidence = Evidence(
            title=e["title"],
            description=e["description"],
            condition=e["condition"],
            source_available=e["source_available"],
        )
        candidates.append(
            Comparable(
                UUID(row["f04_listing_id"]),
                "facebook_marketplace",
                row["external_id"],
                e["title"],
                row["url"],
                Decimal(e["price"]) if e["price"] else None,
                datetime.fromisoformat(row["observed_at"]),
                1,
                evidence,
            )
        )
    target = next(row for row in candidates if row.external_id == "1305432491715538")
    instant = max(row.observed_at for row in candidates)
    result = estimate(target, tuple(candidates), instant)
    assert result.price == Decimal("3900.00")
    assert {row.external_id for row in result.comparables} == {
        "1111757901464370",
        "1186899740658059",
        "2167571404637813",
        "4649777651920127",
        "1124829486993072",
    }
    # A statement about controllers alone cannot establish console functioning.
    accessory = replace(
        candidates[0],
        evidence=Evidence(
            title=TITLE,
            condition="Usado — seminovo",
            source_available=True,
            description="2 controles originais funcionando perfeitamente.",
        ),
    )
    key = identify(target.evidence)
    assert key is not None
    assert not eligible(accessory, key, instant)


def test_duplicates_latest_observation_boundaries_and_rounding() -> None:
    from dataclasses import replace

    target = sample("1300")
    rows = tuple(sample(price) for price in ["2000", "2100", "2200", "2300", "2400", "2400.01"])
    assert estimate(target, rows, NOW).price == Decimal("2250.00")
    assert estimate(
        target,
        tuple(
            replace(row, price=Decimal(price))
            for row, price in zip(
                rows, ["2300", "2300", "2300", "2300.01", "2300.01", "2300.01"], strict=True
            )
        ),
        NOW,
    ).price == Decimal("2300.01")
    old = replace(rows[0], price=Decimal("1"), observed_at=NOW - timedelta(days=1))
    assert estimate(target, rows + (old,), NOW).price == Decimal("2250.00")
    assert estimate(target, rows * 3, NOW).after == 6
    future = replace(rows[0], observed_at=NOW + timedelta(seconds=1), price=Decimal("9999"))
    assert estimate(target, rows + (future,), NOW).price == Decimal("2250.00")


def test_declared_installment_and_multiple_units_are_not_comparables() -> None:
    from dataclasses import replace

    candidate = sample("100")
    key = identify(candidate.evidence)
    assert key is not None
    for description in [
        "Funcionando perfeitamente. 12x de R$ 100,00.",
        "Funcionando perfeitamente. Lote de 2 consoles.",
    ]:
        bad = replace(candidate, evidence=replace(candidate.evidence, description=description))
        assert not eligible(bad, key, NOW)
    # Offering installments does not turn a separately advertised full price into a part-price.
    full = replace(
        candidate,
        price=Decimal("1200"),
        evidence=replace(
            candidate.evidence, description="Funcionando perfeitamente. 12x de R$ 100,00."
        ),
    )
    assert eligible(full, key, NOW)
