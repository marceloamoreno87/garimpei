import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict, cast

from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from tests.factories.listing import ControlledClock, Source, prepare_listing_instance
from tests.factories.runtime import FoundationInstance

FIXED = "2026-11-10T18:00:00+00:00"
TITLE = "PlayStation 5 Slim Digital 825GB"
KEY = "sony:ps5:slim:digital:825gb"


def listing(identity: str, price: str, **overrides: object) -> dict[str, object]:
    return (
        dict(
            external_id=identity,
            url=f"https://www.facebook.com/marketplace/item/{identity}/",
            title=TITLE,
            description="Usado. Funcionando perfeitamente.",
            condition="Usado — seminovo",
            price="R$ " + price,
            published_at=FIXED,
            shipping_offered=True,
            source_available=True,
        )
        | overrides
    )


def base_rows() -> dict[str, dict[str, object]]:
    cases = json.loads((Path(__file__).parents[1] / "fixtures/valuation/cases.json").read_text())
    rows = {
        str(600 + i): listing(str(600 + i), cases["BASE"][f"C{i + 1}"][1].replace(".", ","))
        for i in range(5)
    }
    rows["699"] = listing("699", "1300,00")
    rows["610"] = listing("610", "4200,00")
    rows["611"] = listing("611", "2200,00", title="PlayStation 5 Slim Digital 1TB")
    rows["612"] = listing("612", "2200,00", title="PlayStation 5 Slim Digital")
    rows["613"] = listing("613", "2200,00", description="Não funciona. Com defeito.")
    rows["614"] = listing("614", "2200,00", description=None)
    rows["616"] = listing("616", "0,00", description="Entrada de R$ 100. Usado.")
    return rows


def quote(
    price: str = "3800.00", *, product: str = KEY, url: str = "https://exemplo.invalid/new"
) -> dict[str, object]:
    return dict(
        product=product,
        source="retailer-fixture",
        external_id="N1",
        title=TITLE + " Novo",
        url=url,
        price=price,
        observed_at=FIXED,
        currency="BRL",
        available=True,
    )


@dataclass
class ValuationSource(Source):
    rows: dict[str, dict[str, object]] = field(default_factory=base_rows)
    offers: list[dict[str, object]] = field(
        default_factory=lambda: [quote(), quote("1000", product="wrong")]
    )
    new_failed: bool = False
    collection_failed: bool = False
    new_calls: int = 0

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        self.calls.append((path, parameters.copy()))
        if path == "/new":
            self.new_calls += 1
            if self.pause_path == path:
                self.held.set()
                self.release.wait(30)
            return (503, {}) if self.new_failed else (200, {"offers": self.offers.copy()})
        if path == "/cep":
            from tests.factories.listing import CEP, DATA

            return 200, {"cep": parameters["cep"], "point": DATA["geocoding"][CEP]}
        if self.collection_failed:
            return 503, {}
        if path.startswith("/detail/"):
            identity = path.removeprefix("/detail/")
            if self.rows[identity].get("source_available") is False:
                return 200, {
                    "url": self.rows[identity]["url"],
                    "unavailable": True,
                    "context_cep": parameters["cep"],
                }
            return 200, self.rows[identity] | {"context_cep": parameters["cep"]}
        return 200, dict(
            context={k: v for k, v in parameters.items() if k != "page"},
            cards=list(self.rows.values()),
            next=None,
            end=True,
            empty=False,
        )


def prepare_valuation_instance(
    root: Path, private: Path, url: str
) -> tuple[FoundationInstance, "ControlledClock"]:
    from datetime import datetime

    instance, clock = prepare_listing_instance(root, private, url)
    clock.value = datetime.fromisoformat(FIXED)
    clock.advance(0)
    with instance.private_file.open("a") as file:
        file.write(f"GARIMPEI_VALUATION_FIXTURE_URL={url}\n")
    return instance, clock


class ResaleRecord(TypedDict):
    price: str | None


class Publication(TypedDict):
    id: str
    revision: int
    resale: ResaleRecord


def wait_valuation(
    instance: FoundationInstance, revision: int = 1, *, price: str | None = None
) -> Publication:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        with instance.database() as c:
            row = c.execute(
                "SELECT e.result FROM runtime_valuationprogress p JOIN runtime_listing l ON p.listing_id=l.id JOIN runtime_valuationevaluation e ON p.current_id=e.id WHERE l.external_id='699'"
            ).fetchone()
        if row:
            result = cast(Publication, row[0])
            if int(result["revision"]) >= revision and (
                price is None or result["resale"]["price"] == price
            ):
                return result
        time.sleep(0.2)
    raise AssertionError("F06 worker did not publish the expected target valuation")


def profit_rows() -> dict[str, dict[str, object]]:
    """F07 observations travel through the F04 collector and F06 worker unchanged."""
    rows = base_rows()
    cases = json.loads((Path(__file__).parents[1] / "fixtures/valuation/cases.json").read_text())
    for identity, case in cases["profit"]["offers"].items():
        rows[identity] = listing(
            identity,
            case["price"],
            description="Com defeito. Não funciona.",
            pickup=False,
            delivery=True,
            delivery_cep="01001000",
            freight="R$ 40,00",
            freight_cep="01001000",
        ) | case.get("overrides", {})
    for index in range(5):
        identity = str(800 + index)
        rows[identity] = listing(identity, "101,00", title="PlayStation 5 Slim disco 1TB")
    return rows


@dataclass
class FailingProfitConfiguration:
    """Named technical-failure fake; no private error payload may leave the adapter."""

    def execute(self) -> "MonitoringSnapshot":
        from garimpei.domain.monitoring.errors import ConfigurationReadFailed

        raise ConfigurationReadFailed()
