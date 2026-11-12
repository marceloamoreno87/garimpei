"""Synthetic marketplace for F08; observations and valuations use the actual worker."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from tests.factories.listing import CEP, DATA, ControlledClock, serve
from tests.factories.runtime import FoundationInstance
from tests.factories.valuation import (
    FIXED,
    KEY,
    TITLE,
    ValuationSource,
    listing,
    prepare_valuation_instance,
    quote,
)

CASES = json.loads(
    (Path(__file__).parents[1] / "fixtures/listing/exploration_cases.json").read_text()
)
KEYS = (
    {f"CAM{n:02}": str(10000 + n) for n in range(1, 43)}
    | {f"EXTRA{n}": str(10000 + n) for n in range(43, 48)}
    | {"DEF01": "10048", "INC01": "10049"}
)


def rows() -> dict[str, dict[str, object]]:
    result = {}
    for key, external in KEYS.items():
        n = int(external) - 10000
        profit = (
            Decimal("600")
            if n <= 3
            else Decimal(534 - n)
            if n <= 39
            else Decimal("0")
            if n == 40
            else Decimal("-50")
            if n == 41
            else Decimal(650 + n)
            if n >= 43 and n <= 47
            else None
        )
        price = Decimal("1530") - profit if profit is not None else Decimal("1000")
        camera = n <= 42 or n >= 48
        description = "PlayStation 5 Slim Digital 825GB."
        if n in (5, 42):
            description = "iPhone 13 128GB." if n == 5 else "iPhone 12 64GB."
        result[external] = listing(
            external,
            f"{price:.2f}".replace(".", ","),
            title=f"Câmera {n:02}"
            if n <= 42
            else f"Fone {n}"
            if n <= 47
            else "Câmera com defeito"
            if n == 48
            else "Câmera Incerta",
            description=description,
            condition="Funciona bem" if n <= 47 else "Não funciona" if n == 48 else None,
            published_at=None,
            pickup=True if camera and n <= 42 else False if n <= 47 else None,
            location=DATA["geocoding"][CEP],
            delivery=(n == 4 or 43 <= n <= 47) if n <= 47 else None,
            delivery_cep=CEP,
            freight="R$ 34,00",
            freight_cep=CEP,
            image_url="https://media.exploration.invalid/camera.jpg" if n != 42 else None,
        )
    for product, base, title in (
        (KEY, 20000, TITLE),
        ("apple:iphone13:standard:128gb", 20100, "iPhone 13 128GB"),
    ):
        for n, price in enumerate(CASES["comparables"], 1):
            key = str(base + n)
            result[key] = listing(
                key,
                price.replace(".", ","),
                title=title,
                condition="Usado",
                description="Funcionando perfeitamente.",
                pickup=False,
                delivery=False,
                delivery_cep=CEP,
            )
    return result


@dataclass
class ExplorationSource(ValuationSource):
    rows: dict[str, dict[str, object]] = field(default_factory=rows)
    offers: list[dict[str, object]] = field(default_factory=lambda: [quote("2400.00")])
    empty: bool = False

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        if path not in {"/search"} or self.collection_failed:
            return super().respond(path, parameters)
        self.calls.append((path, parameters.copy()))
        if self.pause_path == path:
            self.held.set()
            self.release.wait(30)
        if self.mode == "partial" and parameters.get("term") == "audio":
            return 503, {}
        camera = parameters.get("term") == "cameras"
        cards = [
            r
            for key, r in self.rows.items()
            if (int(key) <= 10042 or int(key) >= 10048) == camera or int(key) >= 20000
        ]
        if self.empty:
            cards = []
        return 200, dict(
            context={k: v for k, v in parameters.items() if k != "page"},
            cards=cards,
            next=None,
            end=True,
            empty=not cards,
        )

    def change_a(self) -> None:
        self.rows[KEYS["CAM04"]]["price"] = "R$ 700,00"

    def change_b(self) -> None:
        for n in range(39, 43):
            self.rows[KEYS[f"CAM{n:02}"]].update(pickup=False, delivery=True)


def prepare_exploration_instance(
    root: Path, private: Path, source_url: str
) -> tuple[FoundationInstance, ControlledClock]:
    instance, clock = prepare_valuation_instance(root, private, source_url)
    catalog = json.loads(
        (
            root / "apps/backend/src/garimpei/infra/gateway/monitoring/facebook_categories.json"
        ).read_text()
    )
    catalog["entries"].append(
        dict(
            id="audio",
            label="Áudio",
            parent_id=None,
            source_url="https://www.facebook.com/marketplace/category/audio/",
            selectable=True,
        )
    )
    path = private / "catalog.json"
    path.write_text(json.dumps(catalog))
    with instance.private_file.open("a") as file:
        file.write(f"GARIMPEI_CATALOG_FIXTURE={path}\nGARIMPEI_EXPLORATION_INTERVAL_SECONDS=2\n")
    return instance, clock


def configure() -> None:
    from garimpei.infra.persistence.listing_models import Listing
    from garimpei.main import build_monitoring_handler, build_monitoring_queries
    from garimpei.usecase.monitoring.save_step_usecase import StepInput
    from tests.factories.monitoring import require_disposable

    require_disposable()
    now = datetime.fromisoformat(FIXED)
    for key, external in KEYS.items():
        n = int(external) - 10000
        first = now - timedelta(seconds=2 if n == 1 else 1 if n in (2, 3) else 3)
        Listing.objects.create(
            id=UUID(int=n),
            source="facebook_marketplace",
            external_id=external,
            canonical_url=f"https://www.facebook.com/marketplace/item/{external}/",
            first_seen_at=first,
            origin="initial_load",
        )
    handler = build_monitoring_handler()
    handler._save_step.execute(StepInput("regiao", 0, cep=CEP))
    handler._save_step.execute(
        StepInput("custos", 1, shipping_estimate="34.00", resale_fee_percent="10.00")
    )
    form = build_monitoring_queries().read_form()
    assert form is not None
    handler._complete.execute(
        StepInput("interesses", form.revision, category_ids=("cameras", "audio"), product_names=())
    )


def run_lab(directory: Path) -> None:
    import time

    from tests.integration.test_collection import command, completed

    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    source = ExplorationSource()
    with serve(source) as source_url:
        instance, clock = prepare_exploration_instance(
            Path(__file__).resolve().parents[4], directory, source_url
        )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            result = instance.shell(
                "from tests.factories.exploration import configure; configure()"
            )
            assert result.returncode == 0, result.stdout + result.stderr
            completed(instance, 1)
            (directory / "public.json").write_text(
                json.dumps(
                    dict(port=instance.config.web_port, environment=instance.config.environment_id)
                )
            )
            print("F08 lab ready", instance.config.web_port, flush=True)
            applied = ""
            while not (directory / "stop").exists():
                action = (
                    (directory / "action").read_text().strip()
                    if (directory / "action").exists()
                    else ""
                )
                if action and action != applied:
                    if action == "A":
                        source.change_a()
                    if action == "B":
                        source.change_b()
                    if action == "C":
                        source.rows[KEYS["CAM04"]]["source_available"] = False
                    if action == "fail":
                        source.collection_failed = True
                    if action == "recover":
                        source.collection_failed = False
                    clock.advance(61)
                    applied = action
                    print("Action", action, flush=True)
                time.sleep(0.2)
        finally:
            command(instance, "./scripts/stop.sh", "--clean")


if __name__ == "__main__":
    import sys

    run_lab(Path(sys.argv[1]).resolve())
