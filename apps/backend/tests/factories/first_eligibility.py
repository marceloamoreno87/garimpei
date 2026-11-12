"""Owned F16 database and loopback sources; never shares the legacy session fixture."""

import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import TypedDict, cast
from uuid import uuid4

from garimpei.domain.alert.first_eligibility import first_eligibility
from tests.factories.alert import WahaServer, serve_waha
from tests.factories.listing import ControlledClock, serve
from tests.factories.runtime import FoundationInstance, prepare_instance
from tests.factories.valuation import ValuationSource, listing
from tests.integration.test_collection import command, completed, configure, shell, sql, wait_for

TITLE = "PlayStation 5 Slim disco 1TB"
NOW = "2026-11-12T12:00:00+00:00"
type FirstScenario = tuple[FoundationInstance, ValuationSource, ControlledClock, WahaServer]


class FirstRow(TypedDict, total=False):
    price: str
    published_at: str | None
    description: str
    expected_profit: str
    expected: str
    observation: str


class FirstObservation(TypedDict):
    target: str
    comparables: list[str]
    published_at_source: str
    observed_at: str
    manual: str
    automatic: str


class LegacyCases(TypedDict):
    count: int
    states: list[str]
    preserve: list[str]


class DropCases(TypedDict):
    prices: list[str]
    distinct_reductions: int


class FirstCorpus(TypedDict):
    now: str
    BASE: dict[str, FirstRow]
    variations: dict[str, FirstRow]
    LEGADO: LegacyCases
    QUEDAS: DropCases
    observation: FirstObservation
    channel: dict[str, str]
    barrier: dict[str, int]


def first_cases() -> FirstCorpus:
    cases = json.loads(
        (Path(__file__).parents[1] / "fixtures/alert/first_eligibility_cases.json").read_text()
    )
    cases = cast(FirstCorpus, cases)
    validate_first_cases(cases)
    return cases


def validate_first_cases(cases: FirstCorpus) -> None:
    """Fail preparation before any I/O when the contract corpus is inconsistent."""
    now = datetime.fromisoformat(cases["now"])
    assert now.tzinfo is not None
    base = cases["BASE"]
    observation = cases["observation"]
    target = observation["target"]
    comparables = observation["comparables"]
    assert target in base and target not in comparables
    assert len(comparables) == len(set(comparables)) == 5
    assert set(base) == {target, *comparables}
    for row in base.values():
        assert Decimal(row["price"].replace(",", ".")) > 0
        published = row["published_at"]
        assert published is not None and datetime.fromisoformat(published).tzinfo is not None
    resale = sorted(Decimal(base[key]["price"].replace(",", ".")) for key in comparables)[2]
    assert resale == Decimal("1500")
    assert resale * Decimal("0.9") - Decimal(base[target]["price"].replace(",", ".")) == Decimal(
        base[target]["expected_profit"]
    )
    for name in ("exact", "expired", "missing", "future", "untrusted"):
        variation = cases["variations"][name]
        raw = variation["published_at"]
        source: str | None = "fixture.published_at" if raw else None
        try:
            variation_date = datetime.fromisoformat(raw) if raw else None
        except ValueError:
            variation_date, source = None, "fixture.published_at.invalid"
        assert first_eligibility(variation_date, source, now, (), False) == variation["expected"]
    assert observation["published_at_source"] == "fixture.published_at"
    assert datetime.fromisoformat(observation["observed_at"]).tzinfo is not None
    assert cases["channel"]["transport"] == "loopback"
    assert cases["channel"]["recipient"].endswith("@g.us")
    for name in ("zero", "negative"):
        row = cases["variations"][name]
        assert Decimal("1350") - Decimal(row["price"].replace(",", ".")) == Decimal(
            row["expected_profit"]
        )
    assert cases["LEGADO"]["count"] > cases["barrier"]["inventory_batch"]
    assert set(cases["LEGADO"]["states"]) == {
        "confirmed",
        "queued",
        "authorized",
        "uncertain",
        "review",
    }
    prices = [Decimal(value) for value in cases["QUEDAS"]["prices"]]
    assert (
        sum(current < previous for previous, current in zip(prices, prices[1:]))
        == cases["QUEDAS"]["distinct_reductions"]
    )
    exact = cases["variations"]["exact"]["published_at"]
    assert exact is not None and datetime.fromisoformat(exact) <= now
    assert cases["variations"]["missing"]["published_at"] is None


def first_rows() -> dict[str, dict[str, object]]:
    cases = first_cases()
    return {
        identity: listing(
            identity,
            case["price"],
            title=TITLE,
            description=case.get("description", "Funciona perfeitamente."),
            published_at=case.get("published_at"),
            shipping_offered=True,
        )
        for identity, case in cases["BASE"].items()
    }


@contextmanager
def first_eligibility_scenario(
    private: Path, *, enabled: bool = True, sample_ready: bool = True
) -> Iterator[FirstScenario]:
    cases = first_cases()
    source = ValuationSource(rows=first_rows())
    if not sample_ready:
        source.rows["16006"]["description"] = "Com defeito. Não funciona."
    channel = WahaServer(recipient=cases["channel"]["recipient"])
    with serve(source) as url, serve_waha(channel) as waha:
        root = Path(__file__).resolve().parents[4]
        instance = prepare_instance(root, private, "wave11b_f16_" + uuid4().hex[:8])
        clock = ControlledClock(private / "clock", datetime.fromisoformat(NOW))
        clock.advance(0)
        with instance.private_file.open("a") as file:
            file.write(
                f"GARIMPEI_LISTING_INTERVAL=60\nGARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_LISTING_FIXTURE_URL={url}\nGARIMPEI_VALUATION_FIXTURE_URL={url}\nGARIMPEI_LISTING_FIXTURE_CLOCK={clock.path}\nGARIMPEI_ALERTS_ENABLED={str(enabled).lower()}\nGARIMPEI_ALERT_FIXTURE_URL={waha}\nGARIMPEI_WAHA_SESSION=synthetic\nGARIMPEI_WAHA_RECIPIENT=100@g.us\nGARIMPEI_WAHA_ACCOUNT=200@c.us\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance)
            shell(
                instance,
                "from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration; MonitoringConfiguration.objects.filter(slot='active').update(resale_fee_percent='10.00')",
            )
            completed(instance, 1)
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT count(*) FROM runtime_valuationprogress WHERE current_id IS NOT NULL",
                    )
                    == [(6,)]
                ),
                "F16 valuations",
                seconds=45,
            )
            yield instance, source, clock, channel
        except BaseException:
            print(
                "F16 identities",
                sql(
                    instance,
                    "SELECT l.external_id,f.state,f.reason,f.intent_id,f.next_action FROM runtime_firstalertidentity f JOIN runtime_listing l ON l.id=f.listing_id",
                ),
            )
            print(
                "F16 intents",
                sql(
                    instance,
                    "SELECT state,reason,first_decision_id,next_action FROM runtime_alertintent",
                ),
            )
            print("F16 channel calls", channel.calls)
            raise
        finally:
            source.release.set()
            channel.release.set()
            command(instance, "./scripts/stop.sh", "--clean")
