from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.factories.listing import ControlledClock, serve
from tests.factories.runtime import FoundationInstance
from tests.factories.valuation import ValuationSource, prepare_valuation_instance, wait_valuation
from tests.integration.test_collection import command, completed, configure, shell, sql

Scenario = tuple[FoundationInstance, ValuationSource, ControlledClock]


@pytest.fixture
def valuation_scenario(tmp_path: Path) -> Iterator[Scenario]:
    source = ValuationSource()
    root = Path(__file__).resolve().parents[4]
    with serve(source) as url:
        instance, clock = prepare_valuation_instance(root, tmp_path, url)
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance)
            completed(instance, 1)
            yield instance, source, clock
        finally:
            source.release.set()
            command(instance, "./scripts/stop.sh", "--clean")


def read_assert(instance: FoundationInstance, assertions: str) -> None:
    shell(
        instance,
        """
from uuid import UUID,uuid4
from decimal import Decimal
from dataclasses import replace
from garimpei.main import build_read_valuation,build_read_listing
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.valuation_models import ValuationWork,ValuationEvaluation,ValuationProgress
read=build_read_valuation()
target=Listing.objects.get(external_id='699')
v=read.execute(target.id)
assert v is not None
"""
        + assertions,
    )


def test_worker_updates_history_failure_and_resumption(valuation_scenario: Scenario) -> None:
    i, source, clock = valuation_scenario
    first = wait_valuation(i, price="2300.00")
    first_id = str(first["id"])
    read_assert(
        i,
        """
assert v.resale.price==Decimal('2300') and v.currency=='BRL'
assert {r.external_id for r in v.resale.comparables}=={'600','601','602','603','604'}
assert v.new.quote.price==Decimal('3800') and v.new.quote.source=='retailer-fixture'
assert v.method=='median-brl-v1' and v.input_revision==1
assert v.resale.state=='disponivel'
assert all(row.price_kind=='announced' for row in v.resale.comparables) and v.new.quote.price_kind=='announced'
assert read.execute(uuid4()) is None
assert build_read_listing().execute(target.id).observation.evidence.price==Decimal('1300')
assert not hasattr(v,'profit')
""",
    )
    calls = source.new_calls
    read_assert(i, "assert read.execute(target.id).id==v.id\n")
    assert source.new_calls == calls
    source.rows["602"]["price"] = "R$ 2.350,00"
    clock.advance(61)
    completed(i, 2)
    second = wait_valuation(i, int(first["revision"]) + 1, price="2350.00")
    read_assert(
        i,
        f"""
old=read.execute(UUID({first_id!r}),historical=True)
assert old.resale.price==Decimal('2300')
assert next(r.price for r in old.resale.comparables if r.external_id=='602')==Decimal('2300')
assert next(r.price for r in v.resale.comparables if r.external_id=='602')==Decimal('2350')
from garimpei.main import build_valuation_handler
old_work=ValuationEvaluation.objects.get(id=UUID({first_id!r})).work_id
before=ValuationEvaluation.objects.count()
build_valuation_handler().execute(old_work)
assert ValuationEvaluation.objects.count()==before and read.execute(target.id).id==v.id
""",
    )
    source.collection_failed = True
    clock.advance(61)
    completed(i, 3, "unavailable")
    read_assert(
        i,
        f"assert str(v.id)=={str(second['id'])!r} and v.resale.price==Decimal('2350')\nassert v.origin_diagnostic=='falha_de_origem'\n",
    )
    source.collection_failed = False
    source.rows["604"]["source_available"] = False
    clock.advance(61)
    completed(i, 4)
    wait_valuation(i, int(second["revision"]) + 1)
    read_assert(
        i,
        "assert v.resale.price is None and v.resale.reason=='amostra_insuficiente' and v.resale.after==4\nassert v.new.quote.price==Decimal('3800')\nassert build_read_listing().execute(target.id) is not None\n",
    )
    # Retained PostgreSQL state and the real worker survive a normal stop/start.
    command(i, "./scripts/stop.sh")
    source.rows["604"]["source_available"] = True
    clock.advance(61)
    command(i, "./scripts/init.sh", "--disposable")
    completed(i, 5)
    wait_valuation(i, price="2350.00")
    read_assert(i, "assert v.resale.price==Decimal('2350')\n")
    print("SVC-REVENDA-01/04, SVC-NOVO-01, WRK-ATUALIZACAO-01/02/03/04, WRK-PUBLICACAO-02 PASS")


def test_current_validity_new_fallback_and_atomic_rollback(valuation_scenario: Scenario) -> None:
    i, source, clock = valuation_scenario
    first = wait_valuation(i, price="2300.00")
    source.new_failed = True
    # Ask for a retry at seven days, keeping every used observation inside fourteen days.
    source.collection_failed = True
    with i.database() as c:
        c.execute("UPDATE runtime_valuationprogress SET due_at=%s", (clock.value,))
    clock.advance(7 * 86400)
    wait_valuation(i, int(first["revision"]) + 1)
    read_assert(
        i,
        "assert v.resale.price==Decimal('2300')\nassert v.new.quote.price==Decimal('3800') and v.new.failures>=1\n",
    )
    clock.advance(1)
    read_assert(
        i,
        "assert v.resale.price==Decimal('2300') and v.new.quote is None\nassert v.new.state=='fonte_indisponivel'\n",
    )
    source.new_failed = False
    source.offers = []
    with i.database() as c:
        c.execute("UPDATE runtime_valuationprogress SET due_at=%s", (clock.value,))
    clock.advance(1)
    latest = wait_valuation(i, int(first["revision"]) + 2)
    read_assert(i, "assert v.new.state=='sem_referencia' and v.resale.price==Decimal('2300')\n")
    # Expire one confirmed used observation. A new immutable snapshot is captured normally.
    with i.database() as c:
        c.execute(
            "UPDATE runtime_listingobservation SET observed_at=%s WHERE listing_id=(SELECT id FROM runtime_listing WHERE external_id='600')",
            (clock.value.replace(year=2026) - __import__("datetime").timedelta(days=14),),
        )
    value = wait_valuation(i, int(latest["revision"]) + 1)
    read_assert(i, "assert v.resale.price==Decimal('2300')\n")
    # Stop the worker so reading cannot hide the pending invalidity through a fast recompute.
    command(i, "./scripts/stop.sh")
    clock.advance(1)
    command(i, "./scripts/init.sh", "--disposable")
    wait_valuation(i, int(value["revision"]) + 1)
    read_assert(
        i,
        "assert v.resale.price is None and v.resale.reason=='amostra_insuficiente' and v.resale.after==4\n",
    )
    print("SVC-NOVO-02/03/04 and WRK-ATUALIZACAO-05 PASS")


def test_publication_rollback_retains_recoverable_work(valuation_scenario: Scenario) -> None:
    from tests.integration.test_collection import wait_for

    i, source, clock = valuation_scenario
    original = wait_valuation(i, price="2300.00")
    with i.database() as c:
        c.execute("CREATE SEQUENCE valuation_fault_calls")
        c.execute("""CREATE FUNCTION valuation_fault() RETURNS trigger AS $$ BEGIN
            IF NEW.work_id IN (SELECT w.id FROM runtime_valuationwork w JOIN runtime_listing l ON w.listing_id=l.id WHERE l.external_id='699') THEN
              IF nextval('valuation_fault_calls')=1 THEN RAISE EXCEPTION 'controlled_valuation_write_failure'; END IF;
            END IF;
            RETURN NEW; END; $$ LANGUAGE plpgsql""")
        c.execute(
            "CREATE TRIGGER valuation_fault BEFORE INSERT ON runtime_valuationevaluation FOR EACH ROW EXECUTE FUNCTION valuation_fault()"
        )
    source.rows["602"]["price"] = "R$ 2.350,00"
    clock.advance(61)
    completed(i, 2)
    wait_for(
        lambda: bool(
            sql(
                i,
                "SELECT id FROM runtime_valuationwork WHERE diagnostic='valuation_publication_failed' AND listing_id=(SELECT id FROM runtime_listing WHERE external_id='699')",
            )
        ),
        "recoverable failed target publication",
    )
    read_assert(
        i,
        f"assert str(v.id)=={original['id']!r} and v.resale.price==Decimal('2300')\nassert ValuationEvaluation.objects.filter(work__listing=target).count()==1\n",
    )
    command(i, "./scripts/stop.sh")
    clock.advance(6)
    command(i, "./scripts/init.sh", "--disposable")
    wait_valuation(i, int(original["revision"]) + 1, price="2350.00")
    read_assert(
        i,
        """
w=ValuationWork.objects.filter(listing=target).latest('revision')
assert w.completed and w.attempts>=2 and w.requested_at is not None and not w.diagnostic
assert ValuationEvaluation.objects.filter(work__listing=target).count()==2
""",
    )
    assert sql(i, "SELECT last_value FROM valuation_fault_calls")[0][0] == 2
    print(
        "WRK-PUBLICACAO-01/03 PASS: transaction rollback, old version intact, pending work resumed after normal stop"
    )


def test_pending_service_and_indeterminate_product(tmp_path: Path) -> None:
    source = ValuationSource(pause_path="/new")
    with serve(source) as url:
        i, clock = prepare_valuation_instance(Path(__file__).resolve().parents[4], tmp_path, url)
        command(i, "./scripts/init.sh", "--disposable")
        try:
            configure(i)
            completed(i, 1)
            assert source.held.wait(10)
            read_assert(
                i,
                "assert v.id is None and v.resale.price is None and v.resale.reason=='aguardando_avaliacao'\n",
            )
            source.pause_path = None
            source.release.set()
            current = wait_valuation(i, price="2300.00")
            source.rows["699"]["title"] = "PlayStation 5"
            clock.advance(61)
            completed(i, 2)
            wait_valuation(i, int(current["revision"]) + 1)
            read_assert(
                i,
                "assert v.resale.price is None and v.resale.reason=='produto_indeterminado' and v.new.quote is None\nassert build_read_listing().execute(target.id) is not None\n",
            )
        finally:
            source.release.set()
            command(i, "./scripts/stop.sh", "--clean")
    print("SVC-REVENDA-03/07 PASS")


def test_out_of_order_completion_and_additive_migration(valuation_scenario: Scenario) -> None:
    i, source, clock = valuation_scenario
    wait_valuation(i, price="2300.00")
    # Controlled interleaving of two computations uses real PostgreSQL publication.
    read_assert(
        i,
        """
from datetime import timedelta
from django.db import transaction
from django.core.management import call_command
from django.utils.timezone import now
from garimpei.infra.repository.valuation.postgres_repository import PostgresValuationRepository
from garimpei.domain.valuation.policy import estimate
from garimpei.domain.valuation.values import Valuation,NewReference
store=PostgresValuationRepository(lambda _:0)
instant=v.evaluated_at
with transaction.atomic():
    p=ValuationProgress.objects.get(listing=target)
    p.due_at=instant-timedelta(seconds=1)
    p.save()
    store.reconcile(instant)
    old=store.work(ValuationWork.objects.filter(listing=target).latest('revision').id)
    other=Listing.objects.get(external_id='602').latest
    other.price=Decimal('2350')
    other.save(update_fields=['price'])
    store.reconcile(instant)
    new=store.work(ValuationWork.objects.filter(listing=target).latest('revision').id)
assert old and new and new.revision>old.revision
new_value=Valuation(uuid4(),target.id,new.revision,new.target.revision,v.product,instant,estimate(new.target,new.candidates,instant),NewReference('sem_referencia'))
store.publish(new,new_value,instant+timedelta(days=1))
old_value=replace(new_value,id=uuid4(),revision=old.revision,resale=estimate(old.target,old.candidates,instant))
store.publish(old,old_value,instant+timedelta(days=1))
assert read.execute(target.id).id==new_value.id
assert read.execute(target.id).resale.price==Decimal('2350')
assert ValuationEvaluation.objects.filter(work__listing=target).count()==2
ids=list(Listing.objects.order_by('id').values_list('id',flat=True))
# Only the disposable instance's additive F06 tables are reversed for the migration proof.
call_command('migrate','runtime','0005',verbosity=0)
assert list(Listing.objects.order_by('id').values_list('id',flat=True))==ids
call_command('migrate',verbosity=0)
assert list(Listing.objects.order_by('id').values_list('id',flat=True))==ids
assert build_read_listing().execute(target.id).observation.evidence.price==Decimal('1300')
""",
    )
    result = i.command("./scripts/migrate-dev.sh", "--apply")
    assert result.returncode == 0, result.stdout + result.stderr
    print("WRK-PUBLICACAO-02 and additive migration PASS")


def test_published_dispersion_and_current_expiration(valuation_scenario: Scenario) -> None:
    i, source, clock = valuation_scenario
    wait_valuation(i, price="2300.00")
    read_assert(
        i,
        """
from datetime import timedelta
from garimpei.usecase.valuation.read_valuation_usecase import ReadValuationUseCase
from garimpei.infra.queries.valuation.postgres_queries import PostgresValuationQueries
# Read at exactly the inclusive boundary and one second after, with no source I/O.
edge=min(row.observed_at for row in v.resale.comparables)+timedelta(days=14)
assert ReadValuationUseCase(PostgresValuationQueries(),lambda:edge).execute(target.id).resale.price==Decimal('2300')
expired=ReadValuationUseCase(PostgresValuationQueries(),lambda:edge+timedelta(seconds=1)).execute(target.id)
assert expired.resale.price is None and expired.resale.reason=='evidencia_vencida'
assert read.execute(v.id,historical=True).resale.price==Decimal('2300')
""",
    )
    for index, price in enumerate(["1500", "1800", "2200", "2500", "2600"]):
        source.rows[str(600 + index)]["price"] = "R$ " + price + ",00"
    source.rows["610"]["description"] = "Não funciona."
    clock.advance(61)
    completed(i, 2)
    wait_valuation(i, 2)
    read_assert(
        i,
        "assert v.resale.price is None and v.resale.reason=='amostra_dispersa' and v.resale.after==5\n",
    )
    print("SVC-REVENDA-02/05 PASS")


def test_slow_identity_analysis_does_not_hold_the_collection_publication_lock(
    valuation_scenario: Scenario,
) -> None:
    from tests.factories.runtime import pause_worker, resume_worker

    instance, _, _ = valuation_scenario
    wait_valuation(instance)
    group = pause_worker(instance)
    try:
        shell(
            instance,
            """
from threading import Thread,Event
from unittest.mock import patch
from django.db import connection,connections,transaction
from garimpei.infra.repository.valuation.postgres_repository import PostgresValuationRepository
from garimpei.domain.valuation.identity import identify
from garimpei.config.env import load_listing_settings
from garimpei.main import _listing_clock
entered,released=Event(),Event()
errors=[]
def slow_identity(evidence):
    entered.set()
    assert released.wait(10)
    return identify(evidence)
def enqueue(identity): return 1
def reconcile():
    try: PostgresValuationRepository(enqueue).reconcile(_listing_clock(load_listing_settings())())
    except Exception as error: errors.append(type(error).__name__)
    finally: connections.close_all()
with patch('garimpei.infra.repository.valuation.postgres_repository.identify',side_effect=slow_identity):
    worker=Thread(target=reconcile);worker.start()
    try:
        assert entered.wait(5)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_try_advisory_xact_lock(73003)')
                assert cursor.fetchone()[0], 'Price analysis held the shared collection lock'
    finally:
        released.set();worker.join(10)
assert not worker.is_alive() and not errors
""",
        )
    finally:
        resume_worker(group)
