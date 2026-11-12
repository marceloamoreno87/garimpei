import json
from dataclasses import asdict, replace
from pathlib import Path
from uuid import uuid4

from tests.factories.comparable_research import ResearchLoopbackSource, controlled_limits
from tests.factories.listing import CATEGORIES, ControlledClock, serve
from tests.factories.runtime import prepare_instance
from tests.integration.test_collection import command, configure, shell, sql, wait_for


def test_worker_consumes_research_and_publishes_reproducible_profit(tmp_path: Path) -> None:
    source = ResearchLoopbackSource()
    root = Path(__file__).resolve().parents[4]
    from tests.factories.comparable_research import NOW

    clock = ControlledClock(tmp_path / "clock", NOW)
    clock.advance(0)
    with serve(source) as url:
        instance = prepare_instance(root, tmp_path, "f18_worker_" + uuid4().hex[:8])
        # These are explicit controlled-test inputs, never presented as a real measurement.
        evidence = []
        for index in range(2):
            path = tmp_path / f"controlled-{index}.json"
            path.write_text(json.dumps(dict(source_kind="controlled", measurements=[0.01])))
            evidence.append(str(path))
        policy = asdict(
            replace(
                controlled_limits(), environment="eval-controlled", evidence_paths=tuple(evidence)
            )
        )
        limits = tmp_path / "limits.json"
        limits.write_text(json.dumps(policy))
        with instance.private_file.open("a") as file:
            file.write(
                f"GARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERTS_ENABLED=false\nGARIMPEI_LISTING_FIXTURE_URL={url}\nGARIMPEI_VALUATION_FIXTURE_URL={url}\nGARIMPEI_LISTING_FIXTURE_CLOCK={clock.path}\nGARIMPEI_RESEARCH_LIMITS={limits}\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance, active=False)
            shell(
                instance,
                f"""
from garimpei.main import build_monitoring_handler,build_monitoring_queries
from garimpei.usecase.monitoring.save_step_usecase import StepInput
form=build_monitoring_queries().read_form()
build_monitoring_handler()._complete.execute(StepInput('interesses',form.revision,category_ids={CATEGORIES!r},product_names=()))
""",
            )
            wait_for(
                lambda: (
                    sql(instance, "SELECT state FROM runtime_comparableinvestigation")
                    == [("sufficient",)]
                ),
                "F18 worker five retained comparables",
                seconds=45,
            )
            wait_for(
                lambda: bool(
                    sql(
                        instance,
                        "SELECT e.result->'resale'->>'price' FROM runtime_valuationprogress p JOIN runtime_listing l ON l.id=p.listing_id JOIN runtime_valuationevaluation e ON e.id=p.current_id WHERE l.external_id='18801' AND e.result->'resale'->>'price'='2300.00'",
                    )
                ),
                "F18 worker applicable valuation",
                seconds=25,
            )
            shell(
                instance,
                """
from decimal import Decimal
from garimpei.main import build_read_profit
from garimpei.infra.persistence.listing_models import Listing,ListingEvent,ListingInterestMatch
from garimpei.infra.persistence.research_models import ComparableInvestigation
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
l=Listing.objects.get(external_id='18801')
p=build_read_profit().execute(l.id)
assert p.purchase.value==Decimal('1000') and p.resale.value==Decimal('2300')
assert p.fee_percent==Decimal('12.5') and p.fee.value==Decimal('287.50') and p.profit.value==Decimal('1012.50')
r=ComparableInvestigation.objects.get();assert r.pages==1 and r.details==5 and r.attempts==3
refs=Listing.objects.filter(origin='reference');assert refs.count()==5
assert not ListingInterestMatch.objects.filter(observation__listing__in=refs).exists()
assert not ListingEvent.objects.filter(listing__in=refs).exists()
assert MonitoringConfiguration.objects.get(slot='active').monitoringinterest_set.count()==2
""",
            )
            assert sql(
                instance,
                "SELECT queue_name FROM procrastinate_jobs WHERE task_name='garimpei.comparable_research' AND status='succeeded'",
            )
            assert all(float(str(row["seconds"])) >= 0 for row in source.timings)
        except BaseException:
            print(
                "F18 investigations",
                sql(
                    instance,
                    "SELECT product_key,state,reason,pages,details,attempts FROM runtime_comparableinvestigation",
                ),
            )
            print(
                "F18 jobs",
                sql(
                    instance,
                    "SELECT task_name,status FROM procrastinate_jobs ORDER BY id DESC LIMIT 12",
                ),
            )
            log = instance.config.directory / "worker.log"
            if log.exists():
                print("F18 worker log", log.read_text()[-8000:])
            raise
        finally:
            source.release.set()
            command(instance, "./scripts/stop.sh", "--clean")
