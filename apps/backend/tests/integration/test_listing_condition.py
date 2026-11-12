from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.factories.listing import (
    ConditionSource,
    ControlledClock,
    fail_next_condition_write,
    prepare_listing_instance,
    serve,
)
from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker
from tests.integration.test_collection import command, completed, configure, shell, sql, wait_for

type ConditionScenario = tuple[FoundationInstance, ConditionSource, ControlledClock]


@pytest.fixture
def condition_scenario(tmp_path: Path) -> Iterator[ConditionScenario]:
    source = ConditionSource()
    root = Path(__file__).resolve().parents[4]
    with serve(source) as url:
        instance, clock = prepare_listing_instance(root, tmp_path, url)
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance)
            completed(instance, 1)
            # F08 publishes asynchronously; F05 UI regressions start from a readable publication.
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT count(*) FROM runtime_explorationoffer WHERE visible AND revision_id=(SELECT MAX(sequence) FROM runtime_explorationrevision)",
                    )
                    == [(9,)]
                ),
                "initial condition exploration publication",
            )
            yield instance, source, clock
        finally:
            command(instance, "./scripts/stop.sh", "--clean")


def test_condition_projection_updates_and_identity(condition_scenario: ConditionScenario) -> None:
    instance, source, clock = condition_scenario
    shell(
        instance,
        """
from garimpei.infra.persistence.listing_models import Listing
from garimpei.main import build_read_condition,build_condition_queries,build_classify_condition
read=build_read_condition()
expected={'501':'funcionam','502':'defeitos','503':'defeitos','504':'defeitos','505':'defeitos',
          '506':'incerta','507':'incerta','508':'incerta','509':'incerta'}
views=build_condition_queries().all_visible()
assert len(views)==9
for view in views:
    assert view.state.tab==expected[view.external_id]
    assert view.state.manual is None and view.state.revision==0
    assert view.source=='facebook_marketplace'
    assert view.canonical_url==f'https://www.facebook.com/marketplace/item/{view.external_id}/'
    assert read.execute(view.id)==view
a=Listing.objects.get(external_id='506')
assert build_classify_condition().execute(a.id,'good',0)==1
assert build_classify_condition().execute(a.id,'good',1)==1
assert read.execute(a.id).state.satisfies_alert_condition
print('SVC-CONDICAO-01/02/05: nine identities, all partitions, manual alert condition PASS')
""",
    )
    source.rows["INCERTA_A"]["description"] = "Não funciona."
    source.rows["BEM"]["description"] = None
    source.rows["REPUBLICADA"] = source.rows["VAZIA"] | {
        "external_id": "510",
        "url": "https://www.facebook.com/marketplace/item/510/",
    }
    clock.advance(61)
    completed(instance, 2)
    shell(
        instance,
        """
from garimpei.infra.persistence.listing_models import Listing
from garimpei.main import build_read_condition
def read(external):return build_read_condition().execute(Listing.objects.get(external_id=external).id)
a=read('506');new=read('510')
assert a.state.manual=='good' and a.state.tab=='funcionam' and a.state.conflict
assert a.state.analysis.condition=='defect'
assert a.state.analysis.signals[0].text=='Não funciona.'
assert new.id!=a.id and new.state.tab=='incerta' and new.state.revision==0
assert read('501').state.tab=='incerta'
print('SVC-CONDICAO-04/06: contradictory update, new identity, evidence absence PASS')
""",
    )
    source.failed = True
    before = sql(instance, "SELECT id, latest_id FROM runtime_listing ORDER BY external_id")
    clock.advance(61)
    completed(instance, 3, "unavailable")
    assert sql(instance, "SELECT id, latest_id FROM runtime_listing ORDER BY external_id") == before
    assert any(path == "/search" for path, _ in source.calls)


def test_rollback_constraints_and_concurrent_corrections(
    condition_scenario: ConditionScenario,
) -> None:
    instance, _, _ = condition_scenario
    fail_next_condition_write(instance)
    shell(
        instance,
        """
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections,connection,IntegrityError,transaction
from garimpei.domain.listing.condition_ports import ConditionSaveFailed,ConditionConflict
from garimpei.infra.persistence.listing_models import Listing,ManualCondition
from garimpei.main import build_classify_condition,build_read_condition
a=Listing.objects.get(external_id='506');write=build_classify_condition()
try:write.execute(a.id,'good',0)
except ConditionSaveFailed:pass
else:raise AssertionError('fault not surfaced')
assert build_read_condition().execute(a.id).state.revision==0
assert not ManualCondition.objects.filter(listing=a).exists()
with connection.cursor() as cursor:
    cursor.execute('SELECT last_value FROM condition_fault_calls');assert cursor.fetchone()==(1,)
assert write.execute(a.id,'good',0)==1
with connection.cursor() as cursor:cursor.execute('DROP TRIGGER condition_fault ON runtime_manualcondition')
barrier=Barrier(2)
def change():
    close_old_connections();barrier.wait()
    try:return write.execute(a.id,'defect',1)
    except ConditionConflict:return 'conflict'
    finally:close_old_connections()
with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda _:change(),range(2)))
assert sorted(map(str,results))==['2','conflict']
assert build_read_condition().execute(a.id).state.manual=='defect'
for invalid in ({'choice':'other'},{'revision':0}):
    try:
        with transaction.atomic():ManualCondition.objects.filter(listing=a).update(**invalid)
    except IntegrityError:pass
    else:raise AssertionError('CHECK not enforced')
print('rollback, fault activation, two concurrent corrections, database constraints PASS')
""",
    )


def test_migration_preserves_f04_observations(tmp_path: Path) -> None:
    source = ConditionSource()
    root = Path(__file__).resolve().parents[4]
    with serve(source) as url:
        instance, _ = prepare_listing_instance(root, tmp_path, url)
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            configure(instance)
            completed(instance, 1)
            before = sql(
                instance,
                "SELECT id,latest_id,canonical_url FROM runtime_listing WHERE external_id='503'",
            )
            # Current collectors require current columns. Preserve genuine F04 data,
            # then build and upgrade the historical schema with the worker paused.
            group = pause_worker(instance)
            try:
                shell(
                    instance,
                    """
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
MigrationExecutor(connection).migrate([('runtime','0004_listing_publication_window')])
""",
                )
                shell(
                    instance,
                    """
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from garimpei.main import build_read_condition
from garimpei.infra.persistence.listing_models import Listing
executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
view=build_read_condition().execute(Listing.objects.get(external_id='503').id)
assert view.state.tab=='defeitos' and view.state.revision==0
print('migration 0004 -> latest: preexisting F04 identity, evidence and URL retained PASS')
""",
                )
                assert (
                    sql(
                        instance,
                        "SELECT id,latest_id,canonical_url FROM runtime_listing WHERE external_id='503'",
                    )
                    == before
                )
            finally:
                resume_worker(group)
        finally:
            command(instance, "./scripts/stop.sh", "--clean")


def test_collection_in_flight_preserves_manual_choice(
    condition_scenario: ConditionScenario,
) -> None:
    instance, source, clock = condition_scenario
    source.rows["INCERTA_A"]["description"] = "Não funciona."
    source.pause_path = "/detail/506"
    clock.advance(61)
    assert source.held.wait(12), "worker did not reach the controlled detail request"
    try:
        shell(
            instance,
            """
from garimpei.main import build_classify_condition
from garimpei.infra.persistence.listing_models import Listing
assert build_classify_condition().execute(Listing.objects.get(external_id='506').id,'good',0)==1
""",
        )
    finally:
        source.release.set()
    completed(instance, 2)
    shell(
        instance,
        """
from garimpei.main import build_read_condition
from garimpei.infra.persistence.listing_models import Listing
view=build_read_condition().execute(Listing.objects.get(external_id='506').id)
assert view.state.manual=='good' and view.state.revision==1
assert view.state.analysis.condition=='defect' and view.state.conflict
""",
    )
