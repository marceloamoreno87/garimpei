import os
import signal
import time
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from garimpei.infra.runtime.processes import verify_process
from tests.factories.listing import (
    CATEGORIES,
    CEP,
    OTHER_CEP,
    PRODUCT,
    ControlledClock,
    Source,
    prepare_listing_instance,
    serve,
)
from tests.factories.runtime import FoundationInstance

type Scenario = tuple[FoundationInstance, Source, ControlledClock]


@pytest.fixture
def scenario(tmp_path: Path) -> Iterator[Scenario]:
    source = Source()
    root = Path(__file__).resolve().parents[4]
    with serve(source) as url:
        instance, clock = prepare_listing_instance(root, tmp_path, url)
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            yield instance, source, clock
        finally:
            source.release.set()
            command(instance, "./scripts/stop.sh", "--clean")


def command(instance: FoundationInstance, *arguments: str) -> None:
    result = instance.command(*arguments)
    assert result.returncode == 0, result.stdout + result.stderr


def sql(instance: FoundationInstance, statement: str) -> list[tuple[object, ...]]:
    with instance.database() as connection:
        cursor = connection.execute(statement)
        return list(cursor) if cursor.description else []


def wait_for(predicate: Callable[[], bool], description: str, seconds: int = 22) -> None:
    deadline = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() >= deadline:
            pytest.fail(f"Timed out waiting for {description}")
        time.sleep(0.1)


def phase(instance: FoundationInstance) -> list[tuple[object, ...]]:
    return sql(
        instance,
        """
        SELECT cycle.phase, state.initial_completed_at, state.last_success_at, state.generation
        FROM runtime_collectionstate state JOIN runtime_collectioncycle cycle ON cycle.id = state.current_id
    """,
    )


def completed(instance: FoundationInstance, count: int, status: str = "complete") -> None:
    wait_for(
        lambda: (
            sql(
                instance,
                "SELECT count(*) FROM runtime_collectioncycle WHERE finished_at IS NOT NULL",
            )
            == [(count,)]
            and bool(phase(instance))
            and phase(instance)[0][0] == status
        ),
        f"{count} finalized cycles, latest phase {status}",
    )


def shell(instance: FoundationInstance, code: str) -> None:
    result = instance.shell(code)
    assert result.returncode == 0, result.stdout + result.stderr


def configure(instance: FoundationInstance, *, active: bool = True) -> None:
    shell(
        instance,
        f"""
from tests.factories.monitoring import prepare_state
from garimpei.main import build_monitoring_handler, build_monitoring_queries
from garimpei.usecase.monitoring.save_step_usecase import StepInput
assert not prepare_state('RASCUNHO').configured
if {active!r}:
    handler = build_monitoring_handler()
    form = build_monitoring_queries().read_form()
    handler._complete.execute(StepInput('interesses', form.revision,
        category_ids={CATEGORIES!r}, product_names=({PRODUCT!r},)))
""",
    )


def test_initial_service_coverage_and_resume_after_stop(scenario: Scenario) -> None:
    instance, source, clock = scenario
    configure(instance)
    completed(instance, 1)
    assert {
        (request["term"], request["modality"])
        for path, request in source.calls
        if path == "/search"
    } == {(term, modality) for term in (*CATEGORIES, PRODUCT) for modality in ("marketplace",)}
    assert sum(request.get("page") == "second" for _, request in source.calls) == 1
    assert not any(path == "/detail/104" for path, _ in source.calls)
    assert sql(instance, "SELECT external_id FROM runtime_listing ORDER BY external_id") == [
        ("101",),
        ("102",),
        ("103",),
        ("105",),
    ]
    assert sql(
        instance, "SELECT kind, silent, count(*) FROM runtime_listingevent GROUP BY 1, 2"
    ) == [("initial_load", True, 4)]
    shell(
        instance,
        """
from decimal import Decimal
from garimpei.infra.persistence.listing_models import Listing
from garimpei.main import build_read_listing, build_read_listing_changes, build_read_collection_status
reader = build_read_listing()
def read(external_id):
    return reader.execute(Listing.objects.get(external_id=external_id).id)
a, b, c, e = map(read, ("101", "102", "103", "105"))
assert a.id != e.id and a.source == "facebook_marketplace"
assert a.canonical_url == "https://www.facebook.com/marketplace/item/101/"
assert a.observation.evidence.price == Decimal("2300.00") and a.currency == "BRL"
assert a.observation.evidence.title == "PlayStation 5 Slim"
assert a.observation.evidence.condition == "Funciona, marcas de uso"
assert a.observation.evidence.published_at is None and a.first_seen_at is not None
assert len(a.observation.interests) == 2
assert a.current_coverage.pickup == a.current_coverage.shipping == "confirmed"
assert a.applicable_freight == Decimal("32.50")
assert b.observation.evidence.price is None and b.observation.evidence.freight is None
assert b.observation.evidence.condition is None
assert abs(b.current_coverage.distance_km - 20) < 1e-6
assert b.current_coverage.pickup == "confirmed" and b.current_coverage.shipping == "excluded"
assert c.current_coverage.pickup == "excluded" and c.current_coverage.shipping == "unknown"
assert e.current_coverage.pickup == "excluded" and e.current_coverage.shipping == "confirmed"
assert e.observation.evidence.freight == Decimal("20") and e.applicable_freight is None
assert dict(a.observation.provenance)["price"] == "detail"
assert all(x.silent for x in build_read_listing_changes().execute().events)
assert build_read_collection_status().execute().initial_completed_at is not None
""",
    )
    assert "Coleta concluída" in instance.http("/acompanhamento/")[2]
    marker = phase(instance)[0][1]
    a_id = sql(instance, "SELECT id FROM runtime_listing WHERE external_id = '101'")
    command(instance, "./scripts/stop.sh")
    source.mode = "recovery"
    source.price = "R$ 2.200,00"
    source.calls.clear()
    clock.advance(61)
    command(instance, "./scripts/init.sh", "--disposable")
    completed(instance, 2)
    assert phase(instance)[0][1] == marker
    assert sql(instance, "SELECT id FROM runtime_listing WHERE external_id = '101'") == a_id
    assert ("/detail/101", {"cep": CEP}) in source.calls
    shell(
        instance,
        """
from decimal import Decimal
from garimpei.infra.persistence.listing_models import Listing
from garimpei.main import build_read_listing, build_read_listing_changes
events = build_read_listing_changes().execute().events
reduction=next(event for event in events if event.kind=="price_decreased")
discovery=next(event for event in events if event.kind=="discovered")
assert reduction.kind == "price_decreased" and not reduction.silent
assert reduction.previous_price == Decimal("2300") and reduction.price == Decimal("2200")
assert reduction.previous_observation_id != reduction.observation_id
assert discovery.kind == "discovered" and not discovery.silent
new = build_read_listing().execute(discovery.listing_id)
assert new.external_id == "106" and new.current_coverage.pickup == "unknown"
assert new.current_coverage.distance_km is not None and new.current_coverage.pickup_candidate
assert new.current_coverage.pickup_label == "localização aproximada" and new.applicable_freight is None
assert new.current_coverage.shipping == "unknown"
assert new.observation.evidence.published_at > new.first_seen_at.replace(minute=0, second=0)
""",
    )
    for index, (mode, price) in enumerate(
        [
            ("recovery", "R$ 2.200,00"),
            ("missing", None),
            ("recovery", "R$ 2.400,00"),
            ("recovery", "R$ 2.200,00"),
        ],
        start=3,
    ):
        source.mode, source.price = mode, price
        clock.advance(61)
        completed(instance, index)
        if mode == "missing":
            shell(
                instance,
                """
from garimpei.infra.persistence.listing_models import Listing
from garimpei.main import build_read_listing
assert build_read_listing().execute(Listing.objects.get(external_id="101").id).observation.evidence.price is None
""",
            )
    shell(
        instance,
        """
from decimal import Decimal
from garimpei.main import build_read_listing_changes
reader = build_read_listing_changes()
cursor = None
events = []
while page := reader.execute(cursor, 2):
    if not page.events:
        assert page.cursor == cursor
        break
    events.extend(page.events)
    cursor = page.cursor
prices = [item for item in events if item.kind.startswith("price_")]
assert [(x.kind, x.previous_price, x.price) for x in prices] == [
    ("price_decreased", Decimal("2300"), Decimal("2200")),
    ("price_increased", Decimal("2200"), Decimal("2400")),
    ("price_decreased", Decimal("2400"), Decimal("2200")),
]
assert len({x.id for x in prices}) == 3
assert reader.execute(prices[0].sequence - 1, 1).events[0].id == prices[0].id
""",
    )


def test_verified_empty_and_partial_retry(scenario: Scenario) -> None:
    instance, source, clock = scenario
    source.mode = "empty"
    configure(instance)
    completed(instance, 1)
    initial = phase(instance)[0][1:3]
    assert initial[0] is not None
    assert sql(instance, "SELECT count(*) FROM runtime_listing") == [(0,)]
    source.mode = "partial"
    clock.advance(61)
    completed(instance, 2, "partial")
    assert phase(instance)[0][1:3] == initial
    assert sql(instance, "SELECT count(*) FROM runtime_listing") == [(3,)]
    page = instance.http("/acompanhamento/")[2]
    assert "Coleta parcial" in page and "Última coleta completa" in page
    assert "Revisar configurações" in page

    source.mode = "limited"
    clock.advance(61)
    completed(instance, 3, "partial")
    assert sql(
        instance,
        """
        SELECT extract(epoch FROM state.next_attempt_at - cycle.finished_at)
        FROM runtime_collectionstate state JOIN runtime_collectioncycle cycle ON cycle.id = state.current_id
    """,
    ) == [(90,)]
    calls = len(source.calls)
    clock.advance(89)
    time.sleep(2.2)
    assert len(source.calls) == calls
    source.mode = "repeated"
    clock.advance(1)
    completed(instance, 4, "partial")
    assert any(
        "repeated_page" in str(row)
        for row in sql(
            instance,
            "SELECT cycle.results FROM runtime_collectionstate state JOIN runtime_collectioncycle cycle ON cycle.id = state.current_id",
        )
    )


def test_lease_and_new_scope_fence_old_worker(scenario: Scenario) -> None:
    instance, source, clock = scenario
    configure(instance)
    completed(instance, 1)
    baseline = phase(instance)[0][1]
    source.pause_path = "/detail/101"
    source.price = "R$ 1.900,00"
    clock.advance(61)
    assert source.held.wait(10)
    source.price = "R$ 2.200,00"
    clock.advance(21)
    completed(instance, 2)
    source.release.set()
    assert sql(instance, "SELECT price FROM runtime_listingobservation WHERE price = 1900") == []
    assert sql(
        instance, "SELECT count(*) FROM runtime_listingevent WHERE kind = 'price_decreased'"
    ) == [(1,)]
    source.held.clear()
    source.release.clear()
    source.pause_path = "/search"
    clock.advance(61)
    assert source.held.wait(10)
    shell(
        instance,
        f"""
from garimpei.main import build_monitoring_handler, build_read_monitoring_configuration, build_read_listing
from garimpei.infra.persistence.listing_models import Listing
from garimpei.usecase.monitoring.save_step_usecase import StepInput
current = build_read_monitoring_configuration().execute()
build_monitoring_handler()._update.execute(StepInput(
    "editar", current.revision, cep={OTHER_CEP!r}, shipping_estimate="25.50",
    resale_fee_percent="12.50", product_names=("Notebook",),
))
a = build_read_listing().execute(Listing.objects.get(external_id="101").id)
assert a.current_coverage.shipping == "unknown" and not a.scope_current
""",
    )
    source.mode = "edited"
    # New scope starts independently of the old network request or next-attempt time.
    completed(instance, 4)
    source.release.set()
    assert phase(instance)[0][1] == baseline
    assert {
        (r["term"], r["cep"]) for p, r in source.calls if p == "/search" and r["cep"] == OTHER_CEP
    } == {
        ("Notebook", OTHER_CEP),
    }
    assert sql(instance, "SELECT count(*) FROM runtime_listingevent WHERE kind = 'discovered'") == [
        (0,)
    ]


def test_rollback_and_restart_after_first_batch(scenario: Scenario) -> None:
    instance, source, clock = scenario
    source.mode = "many"
    sql(
        instance,
        """
        CREATE FUNCTION f04_batch_gate() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
          IF EXISTS(SELECT 1 FROM runtime_listing WHERE id = NEW.listing_id AND external_id='220') THEN
             PERFORM pg_sleep(45);
          END IF;
          RETURN NEW;
        END $$;
        CREATE TRIGGER f04_batch_gate BEFORE INSERT ON runtime_listingevent
        FOR EACH ROW EXECUTE FUNCTION f04_batch_gate();
    """,
    )
    configure(instance)
    wait_for(
        lambda: (
            sql(instance, "SELECT count(*) FROM runtime_listingevent") == [(20,)]
            and bool(
                sql(
                    instance,
                    "SELECT pid FROM pg_stat_activity WHERE datname=current_database() AND wait_event = 'PgSleep'",
                )
            )
        ),
        "first committed batch and second batch held before the event commit",
    )
    assert phase(instance)[0][1] is None
    assert sql(instance, "SELECT count(*) FROM runtime_listingobservation") == [(20,)]
    confirmed_ids = sql(instance, "SELECT external_id FROM runtime_listing ORDER BY external_id")
    assert confirmed_ids == [(str(identity),) for identity in range(200, 220)]
    confirmed_observations = sql(instance, "SELECT * FROM runtime_listingobservation ORDER BY id")
    confirmed_events = sql(instance, "SELECT * FROM runtime_listingevent ORDER BY id")
    worker = next(
        record for record in instance.manifest["processes"] if "runworker" in record["command"]
    )
    verify_process(worker, instance.root)
    os.kill(worker["pid"], signal.SIGKILL)
    # PostgreSQL may finish the sleeping trigger before it notices the disconnected worker.
    sql(
        instance,
        "SELECT pg_cancel_backend(pid) FROM pg_stat_activity WHERE datname=current_database() AND wait_event='PgSleep'",
    )
    sql(
        instance,
        "DROP TRIGGER f04_batch_gate ON runtime_listingevent; DROP FUNCTION f04_batch_gate()",
    )
    assert sql(instance, "SELECT count(*) FROM runtime_listingobservation") == [(20,)]
    assert sql(instance, "SELECT count(*) FROM runtime_listingevent") == [(20,)]
    assert phase(instance)[0][2] is None
    command(instance, "./scripts/stop.sh")
    calls_before = len(source.calls)
    clock.advance(21)
    command(instance, "./scripts/init.sh", "--disposable")
    completed(instance, 1)
    resumed_calls = source.calls[calls_before:]
    assert not any(path == "/search" for path, _ in resumed_calls)
    resumed_details = [path for path, _ in resumed_calls if path.startswith("/detail/")]
    assert len(resumed_details) == 5
    assert set(resumed_details) == {f"/detail/{identity}" for identity in range(220, 225)}
    assert (
        sql(
            instance,
            "SELECT o.* FROM runtime_listingobservation o JOIN runtime_listing l "
            "ON l.id=o.listing_id WHERE l.external_id::integer < 220 ORDER BY o.id",
        )
        == confirmed_observations
    )
    assert (
        sql(
            instance,
            "SELECT e.* FROM runtime_listingevent e JOIN runtime_listing l "
            "ON l.id=e.listing_id WHERE l.external_id::integer < 220 ORDER BY e.id",
        )
        == confirmed_events
    )
    assert sql(instance, "SELECT count(*) FROM runtime_listingevent WHERE silent") == [(25,)]
    assert sql(instance, "SELECT count(*) FROM runtime_listingobservation") == [(25,)]


def test_initial_partial_and_scope_change_preserve_silence(scenario: Scenario) -> None:
    instance, source, _ = scenario
    source.mode = "access"
    configure(instance)
    completed(instance, 1, "partial")
    assert phase(instance)[0][1:3] == (None, None)
    assert sql(instance, "SELECT access_suspended FROM runtime_collectionstate") == [(True,)]
    assert sql(instance, "SELECT DISTINCT kind, silent FROM runtime_listingevent") == [
        ("initial_load", True)
    ]
    old_ids = set(sql(instance, "SELECT id FROM runtime_listing"))
    source.mode = "edited"
    shell(
        instance,
        f"""
from garimpei.main import build_monitoring_handler, build_read_monitoring_configuration
from garimpei.usecase.monitoring.save_step_usecase import StepInput
current = build_read_monitoring_configuration().execute()
build_monitoring_handler()._update.execute(StepInput(
    "editar", current.revision, cep={OTHER_CEP!r}, shipping_estimate="25.50",
    resale_fee_percent="12.50", product_names=("Notebook",),
))
""",
    )
    completed(instance, 2)
    assert old_ids < set(sql(instance, "SELECT id FROM runtime_listing"))
    assert sql(instance, "SELECT DISTINCT kind, silent FROM runtime_listingevent") == [
        ("initial_load", True)
    ]
    assert sql(
        instance,
        """
        SELECT state.initial_scope = cycle.scope_key
        FROM runtime_collectionstate state JOIN runtime_collectioncycle cycle ON cycle.id = state.current_id
    """,
    ) == [(True,)]


def test_migration_preserves_confirmed_f03(scenario: Scenario) -> None:
    instance, source, _ = scenario
    shell(
        instance,
        """
from django.core.management import call_command
from tests.factories.monitoring import prepare_state
from garimpei.main import build_read_monitoring_configuration
call_command("migrate", "runtime", "0002", verbosity=0)
snapshot = prepare_state("ATIVA")
assert snapshot.configured
call_command("migrate", "runtime", verbosity=0)
assert build_read_monitoring_configuration().execute() == snapshot
""",
    )
    completed(instance, 1)
    assert any(path == "/search" for path, _ in source.calls)


def test_exact_48_hour_window_out_of_order_and_legacy_evidence(scenario: Scenario) -> None:
    instance, source, clock = scenario
    source.mode = "window"
    configure(instance)
    completed(instance, 1)
    assert sql(instance, "SELECT external_id FROM runtime_listing ORDER BY external_id") == [
        ("108",),
        ("110",),
    ]
    shell(
        instance,
        """
from datetime import UTC, datetime
from garimpei.main import build_read_collection_status, build_read_listing
from garimpei.infra.persistence.listing_models import Listing, ListingObservation
status=build_read_collection_status().execute()
assert status.window_start == datetime(2025,12,30,12,tzinfo=UTC)
assert status.window_end == datetime(2026,1,1,12,tzinfo=UTC)
assert len(status.window_proofs) == 3
identity=Listing.objects.get(external_id="108").id
view=build_read_listing().execute(identity)
assert view.current_coverage.shipping_candidate
assert view.current_coverage.shipping_label == "entrega no CEP a confirmar"
# Legacy observations predate the new optional fields and remain readable.
row=ListingObservation.objects.get(id=view.observation.id)
row.evidence.pop("shipping_offered",None)
row.evidence.pop("shipping_evidence",None)
row.evidence.pop("pickup_scope_verified",None)
row.evidence.pop("source_available",None)
row.evidence.pop("availability_evidence",None)
row.coverage={key:value for key,value in row.coverage.items() if key in {
 "pickup","shipping","distance_km","pickup_reason","shipping_reason",
}}
row.save(update_fields=["evidence","coverage"])
assert build_read_listing().execute(identity).observation.evidence.shipping_offered is None
assert build_read_listing().execute(identity).observation.evidence.source_available is None
""",
    )

    marker = phase(instance)[0][1]
    source.mode = "window_revisit"
    source.calls.clear()
    clock.advance(48 * 3600 + 61)
    completed(instance, 2)
    assert phase(instance)[0][1] == marker
    assert {path for path, _ in source.calls if path.startswith("/detail/")} == {
        "/detail/108",
        "/detail/110",
    }
    assert sql(instance, "SELECT count(*) FROM runtime_listingobservation") == [(4,)]
    assert sql(instance, "SELECT kind, count(*) FROM runtime_listingevent GROUP BY kind") == [
        ("initial_load", 2),
    ]


def test_confirmed_unavailable_preserves_history_and_can_finish_initial_load(
    scenario: Scenario,
) -> None:
    instance, source, clock = scenario
    source.mode = "partial"
    configure(instance)
    completed(instance, 1, "partial")
    assert phase(instance)[0][1] is None
    identities = sql(instance, "SELECT id FROM runtime_listing ORDER BY external_id")
    source.mode = "withdrawn"
    clock.advance(61)
    completed(instance, 2)
    marker = phase(instance)[0][1]
    assert marker is not None
    assert sql(instance, "SELECT id FROM runtime_listing ORDER BY external_id") == identities
    shell(
        instance,
        """
from decimal import Decimal
from garimpei.main import build_read_listing, build_read_listing_changes
from garimpei.infra.persistence.listing_models import Listing
for identity in ("101", "103"):
    row = Listing.objects.get(external_id=identity)
    view = build_read_listing().execute(row.id)
    assert view.observation.evidence.source_available is False
    assert view.observation.evidence.availability_evidence == "source_unavailable_product"
    assert view.observation.evidence.price is None
    assert view.current_coverage.status == "excluded"
    assert view.stale_reason == "listing_unavailable"
    assert view.last_valid_observation is not None
    assert view.last_valid_observation.evidence.price == (Decimal("2300") if identity == "101" else None)
    assert row.known_price_id != row.latest_id
assert all(event.kind == "initial_load" and event.silent for event in build_read_listing_changes().execute().events)
""",
    )
    source.mode, source.price = "recovery", "R$ 2.200,00"
    clock.advance(61)
    completed(instance, 3)
    assert phase(instance)[0][1] == marker
    shell(
        instance,
        """
from decimal import Decimal
from garimpei.main import build_read_listing, build_read_listing_changes
from garimpei.infra.persistence.listing_models import Listing
row=Listing.objects.get(external_id="101")
view=build_read_listing().execute(row.id)
assert view.observation.evidence.source_available is True
assert view.stale_reason is None
reductions=[event for event in build_read_listing_changes().execute().events if event.kind == "price_decreased"]
assert len(reductions)==1
assert reductions[0].previous_price == Decimal("2300") and reductions[0].price == Decimal("2200")
""",
    )


def test_details_are_published_before_next_interest_finishes(scenario: Scenario) -> None:
    instance, source, _ = scenario
    source.pause_path = "/search"
    source.pause_term = "cameras"
    configure(instance)
    assert source.held.wait(10)
    assert phase(instance)[0][0] == "running"
    published = sql(
        instance,
        "SELECT l.external_id FROM runtime_listingobservation o "
        "JOIN runtime_listing l ON l.id=o.listing_id",
    )
    assert len(published) >= 1
    assert ("101",) in published
    assert sql(instance, "SELECT count(*) FROM runtime_listingevent WHERE NOT silent") == [(0,)]
    source.release.set()
    completed(instance, 1)
    assert sql(instance, "SELECT count(*) FROM runtime_listingobservation") == [(4,)]
    assert sum(path == "/detail/101" for path, _ in source.calls) == 1
    shell(
        instance,
        """
from garimpei.infra.persistence.listing_models import Listing
row = Listing.objects.get(external_id='101')
assert row.latest.matches.count() == 2
assert row.observations.count() == 1
""",
    )


def test_proven_new_listing_can_alert_with_initial_history_partial(scenario: Scenario) -> None:
    instance, source, clock = scenario
    source.mode = "fresh_partial"
    configure(instance)
    completed(instance, 1, "unavailable")
    assert phase(instance)[0][1] is None
    clock.advance(61)
    completed(instance, 2, "partial")
    assert phase(instance)[0][1] is None
    assert sql(
        instance, "SELECT kind, silent, count(*) FROM runtime_listingevent GROUP BY 1,2"
    ) == [("discovered", False, 1), ("initial_load", True, 1)]
    marker = sql(instance, "SELECT monitoring_started_at FROM runtime_collectionstate")
    command(instance, "./scripts/stop.sh")
    clock.advance(61)
    command(instance, "./scripts/init.sh", "--disposable")
    completed(instance, 3, "partial")
    assert sql(instance, "SELECT monitoring_started_at FROM runtime_collectionstate") == marker
    assert sql(instance, "SELECT count(*) FROM runtime_listingevent WHERE kind='discovered'") == [
        (1,)
    ]


def test_policy_adoption_preserves_history_receipts_and_sets_a_safe_boundary(
    scenario: Scenario,
) -> None:
    from tests.factories.runtime import pause_worker, resume_worker

    instance, _, _ = scenario
    configure(instance)
    completed(instance, 1)
    group = pause_worker(instance)
    try:
        shell(
            instance,
            """
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from garimpei.infra.persistence.listing_models import Listing,ListingEvent,CollectionState
from garimpei.infra.persistence.alert_models import AlertEventDecision,AlertIntent
now=timezone.now()
listing=Listing.objects.get(external_id='101')
Listing.objects.filter(id=listing.id).update(origin='discovered')
event=ListingEvent.objects.filter(listing=listing).first()
decision,_=AlertEventDecision.objects.get_or_create(event=event,defaults={'next_action':now})
receipt=AlertIntent.objects.create(decision=decision,state='confirmed',next_action=now,created_at=now,
    confirmed_at=now,confirmed_ack=1,confirmed_message='synthetic-preserved-receipt',body='historical frozen message')
before_events=list(ListingEvent.objects.values_list('id','kind','silent'))
MigrationExecutor(connection).migrate([('runtime','0011_facebook_browser_profile')])
cutover=timezone.now()
executor=MigrationExecutor(connection)
target=[('runtime','0012_opportunity_collection')]
executor.migrate(target)
historical_state=executor.loader.project_state(target).apps.get_model('runtime','CollectionState')
state=historical_state.objects.get()
assert cutover <= state.monitoring_started_at <= timezone.now()
assert list(ListingEvent.objects.values_list('id','kind','silent'))==before_events
assert Listing.objects.get(id=listing.id).discovery_emitted
assert not Listing.objects.get(external_id='102').discovery_emitted
# Current ORM includes additive fields from subsequent features.
executor=MigrationExecutor(connection)
executor.migrate(executor.loader.graph.leaf_nodes())
preserved=AlertIntent.objects.get(id=receipt.id)
assert preserved.state=='confirmed' and preserved.confirmed_message=='synthetic-preserved-receipt'
assert preserved.confirmed_ack==1 and preserved.body=='historical frozen message'
""",
        )
    finally:
        resume_worker(group)


def test_incomplete_pagination_does_not_accumulate_network_backoff(scenario: Scenario) -> None:
    instance, source, clock = scenario
    source.mode = "repeated"
    configure(instance)
    for count in range(1, 4):
        if count > 1:
            clock.advance(61)
        completed(instance, count, "partial")
    source.mode = "partial"
    clock.advance(61)
    completed(instance, 4, "partial")
    assert sql(
        instance,
        """
        SELECT s.failures, extract(epoch FROM s.next_attempt_at-c.finished_at)
        FROM runtime_collectionstate s JOIN runtime_collectioncycle c ON c.id=s.current_id
    """,
    ) == [(0, 60)]

    sql(
        instance,
        """
        UPDATE runtime_collectionstate SET failures=8,
        next_attempt_at=(SELECT finished_at+interval '1 hour' FROM runtime_collectioncycle WHERE id=current_id)
    """,
    )
    clock.advance(1)
    wait_for(
        lambda: (
            sql(
                instance,
                """
        SELECT s.failures, extract(epoch FROM s.next_attempt_at-c.finished_at)
        FROM runtime_collectionstate s JOIN runtime_collectioncycle c ON c.id=s.current_id
    """,
            )
            == [(0, 60)]
        ),
        "old hour-long backoff replaced by regular cadence",
    )


def test_repeated_detail_errors_pause_after_three_attempts_and_recover(scenario: Scenario) -> None:
    instance, source, clock = scenario
    source.mode = "many_details_down"
    configure(instance)
    completed(instance, 1, "unavailable")
    assert sum(path.startswith("/detail/") for path, _ in source.calls) == 3
    assert sql(instance, "SELECT count(*) FROM runtime_collectioncandidate") == [(0,)]
    source.mode = "many"
    clock.advance(6)
    completed(instance, 2)
    assert sql(instance, "SELECT count(*) FROM runtime_listingobservation") == [(25,)]
