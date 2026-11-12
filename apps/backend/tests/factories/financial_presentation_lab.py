"""Owned F20 synthetic lab. Run with --private-dir, JSON actions on stdin."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from tests.factories.alert import WahaServer, serve_waha
from tests.factories.exploration import ExplorationSource, prepare_exploration_instance
from tests.factories.listing import CEP, DATA, serve
from tests.factories.valuation import listing, quote
from tests.integration.test_collection import command, completed, shell, sql, wait_for

FIXTURE = Path(__file__).parents[1] / "fixtures/valuation/financial_presentation.json"


def financial_rows() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for n in range(1, 43):
        price = (
            str(1000 + 5 * (n - 1))
            if n < 40
            else "1350"
            if n == 40
            else "1400"
            if n == 41
            else "1000"
        )
        result[str(10000 + n)] = listing(
            str(10000 + n),
            price + ",00",
            title=f"Oferta {n:02}",
            description="Usado. Funcionando perfeitamente. PlayStation 5 Slim Digital 825GB. frete conforme vendedor."
            if n != 42
            else "Usado. Funcionando perfeitamente. iPhone 12 64GB.",
            pickup=True,
            delivery=False,
            location=DATA["geocoding"][CEP],
            condition="Funciona bem",
        )
    result["10043"] = listing(
        "10043",
        "0,00",
        title="Sem compra",
        condition="Funciona bem",
        description="Funcionando perfeitamente. PlayStation 5 Slim Digital 825GB.",
        pickup=True,
        delivery=False,
    )
    result["10043"]["price"] = None
    result["10044"] = listing(
        "10044",
        "70,00",
        title="Fração",
        condition="Funciona bem",
        description="Funcionando perfeitamente. iPhone 13 128GB.",
        pickup=True,
        delivery=False,
    )
    for n, price in enumerate(json.loads(FIXTURE.read_text())["comparables"], 1):
        result[str(20000 + n)] = listing(
            str(20000 + n), price.replace(".", ","), pickup=False, delivery=False
        )
        result[str(20100 + n)] = listing(
            str(20100 + n), "101,00", title="iPhone 13 128GB", pickup=False, delivery=False
        )
    return result


@dataclass
class FinancialSource(ExplorationSource):
    rows: dict[str, dict[str, object]] = field(default_factory=financial_rows)
    offers: list[dict[str, object]] = field(
        default_factory=lambda: [
            quote("2400.00"),
            quote("2400.00", product="apple:iphone12:standard:64gb"),
        ]
    )

    def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
        if path != "/search":
            return super().respond(path, parameters)
        return 200, dict(
            context={k: v for k, v in parameters.items() if k != "page"},
            cards=list(self.rows.values()),
            next=None,
            end=True,
            empty=False,
        )


def configure_financial() -> None:
    from garimpei.main import build_monitoring_handler, build_monitoring_queries
    from garimpei.usecase.monitoring.save_step_usecase import StepInput
    from tests.factories.monitoring import require_disposable

    require_disposable()
    handler = build_monitoring_handler()
    handler._save_step.execute(StepInput("regiao", 0, cep="01001000"))
    handler._save_step.execute(StepInput("custos", 1, resale_fee_percent="10"))
    form = build_monitoring_queries().read_form()
    assert form is not None
    handler._complete.execute(StepInput("interesses", form.revision, category_ids=("cameras",)))


def publish_and_check(instance: FoundationInstance) -> None:
    wait_for(
        lambda: (
            sql(
                instance,
                """SELECT count(*) FROM runtime_listing l
            LEFT JOIN runtime_valuationprogress p ON p.listing_id=l.id
            LEFT JOIN runtime_valuationevaluation e ON e.id=p.current_id
            LEFT JOIN runtime_valuationwork w ON w.id=e.work_id
            WHERE p.requested IS NULL OR w.revision IS DISTINCT FROM p.requested""",
            )
            == [(0,)]
        ),
        "all financial valuation heads settled",
        seconds=60,
    )
    shell(
        instance,
        "from garimpei.main import build_publish_exploration; build_publish_exploration().execute()",
    )
    wait_for(
        lambda: "R$ 350,00" in instance.http("/ofertas/?q=Oferta")[2],
        "financial publication",
        seconds=60,
    )


def set_fee(value: str) -> None:
    from garimpei.main import build_monitoring_handler, build_read_monitoring_configuration
    from garimpei.usecase.monitoring.save_step_usecase import StepInput
    from tests.factories.monitoring import require_disposable

    require_disposable()
    current = build_read_monitoring_configuration().execute()
    if not current.configured or current.revision is None or current.cep is None:
        raise ValueError("fee: expected a completed synthetic configuration")
    build_monitoring_handler()._update.execute(
        StepInput(
            "editar",
            current.revision,
            cep=current.cep,
            resale_fee_percent=value,
            category_ids=current.category_ids,
            product_names=current.product_names,
        )
    )


def run_lab(private: Path, *, configured: bool = True) -> None:
    from tests.factories.runtime import pause_worker, resume_worker

    private.mkdir(mode=0o700, parents=True, exist_ok=True)
    source, channel = FinancialSource(), WahaServer()
    root = Path(__file__).resolve().parents[4]
    with serve(source) as origin, serve_waha(channel) as waha:
        instance, clock = prepare_exploration_instance(root, private, origin)
        with instance.private_file.open("a") as out:
            out.write(
                f"GARIMPEI_ALERTS_ENABLED=true\nGARIMPEI_ALERT_FIXTURE_URL={waha}\nGARIMPEI_WAHA_SESSION=synthetic\nGARIMPEI_WAHA_RECIPIENT=100@c.us\nGARIMPEI_WAHA_ACCOUNT=200@c.us\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        failed = False
        try:
            if configured:
                shell(
                    instance,
                    "from tests.factories.financial_presentation_lab import configure_financial; configure_financial()",
                )
                completed(instance, 1)
                publish_and_check(instance)
            metadata = {
                "url": f"http://127.0.0.1:{instance.config.web_port}",
                "environment_id": instance.config.environment_id,
                "private_file": str(instance.private_file),
                "ids": {
                    str(row[0]): str(row[1])
                    for row in sql(instance, "SELECT external_id,id::text FROM runtime_listing")
                },
            }
            (private / "public.json").write_text(json.dumps(metadata))
            print(json.dumps(metadata), flush=True)
            while True:
                action = json.loads(input())
                name = action["action"]
                if name == "quit":
                    break
                if name == "fail_read":
                    sql(
                        instance,
                        "ALTER TABLE runtime_explorationoffer RENAME TO runtime_explorationoffer_f20_fault",
                    )
                    failed = True
                if name == "recover_read":
                    sql(
                        instance,
                        "ALTER TABLE runtime_explorationoffer_f20_fault RENAME TO runtime_explorationoffer",
                    )
                    failed = False
                if name == "fee":
                    shell(
                        instance,
                        "from tests.factories.financial_presentation_lab import set_fee; set_fee("
                        + repr(str(action["value"]))
                        + ")",
                    )
                    clock.advance(61)
                if name == "new_offer":
                    identity = str(action.get("key", "10951"))
                    if not identity.isdecimal():
                        raise ValueError("key: expected synthetic decimal identity")
                    clock.advance(1)
                    source.rows[identity] = listing(
                        identity,
                        str(action.get("price", "1000,00")),
                        title=str(action.get("title", "PlayStation 5 Slim Digital 825GB")),
                        description="Funcionando perfeitamente.",
                        condition="Funciona bem",
                        pickup=True,
                        delivery=False,
                        published_at=clock.value.isoformat(),
                    )
                    clock.advance(61)
                if name == "update":
                    source.rows["10001"]["price"] = "R$ 900,00"
                    for n in range(1, 6):
                        source.rows[str(20000 + n)]["price"] = "R$ " + str(1450 + n * 50) + ",00"
                    clock.advance(61)
                if name == "incompatible":
                    shell(
                        instance,
                        "from garimpei.infra.persistence.exploration_models import ExplorationOffer; from uuid import uuid4; r=ExplorationOffer.objects.filter(listing__external_id='10001').latest('revision_id'); r.payload['composition']['observation_id']=str(uuid4()); r.save(update_fields=['payload'])",
                    )
                if name == "restart":
                    command(instance, "./scripts/stop.sh")
                    command(instance, "./scripts/init.sh", "--disposable")
                if name == "pause_worker":
                    group = pause_worker(instance)
                    (private / "worker-group").write_text(str(group))
                if name == "resume_worker":
                    resume_worker(int((private / "worker-group").read_text()))
                print(
                    json.dumps(
                        {
                            "action": name,
                            "messages": len(channel.messages),
                            "posts": len([c for c in channel.calls if c[0] == "POST"]),
                            "revision": str(
                                sql(
                                    instance,
                                    "SELECT id FROM runtime_explorationrevision ORDER BY sequence DESC LIMIT 1",
                                )[0][0]
                            ),
                        }
                    ),
                    flush=True,
                )
        finally:
            if failed:
                sql(
                    instance,
                    "ALTER TABLE runtime_explorationoffer_f20_fault RENAME TO runtime_explorationoffer",
                )
            if (private / "worker-group").exists():
                resume_worker(int((private / "worker-group").read_text()))
            command(instance, "./scripts/stop.sh", "--clean")


from tests.factories.runtime import FoundationInstance  # noqa:E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-dir", type=Path, required=True)
    parser.add_argument("--unconfigured", action="store_true")
    args = parser.parse_args()
    run_lab(args.private_dir.resolve(), configured=not args.unconfigured)
