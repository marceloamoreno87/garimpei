"""F08 owns an MVCC snapshot, not a configuration lock spanning compilation."""

from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker


def _checked_shell(instance: FoundationInstance, code: str) -> None:
    result = instance.shell(code)
    assert result.returncode == 0, result.stdout + result.stderr
    for line in result.stdout.splitlines():
        if line.startswith(("F08", "Opt-in")):
            print(line)


def test_exploration_snapshot_allows_configuration_commit_and_serializes_publishers(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(tmp_path, enabled=False) as (instance, _, _, channel):
        group = pause_worker(instance)
        try:
            _checked_shell(
                instance,
                """
from concurrent.futures import ThreadPoolExecutor
from threading import Event,Lock
from time import monotonic,sleep
from decimal import Decimal
from unittest.mock import patch
from django.db import connection,connections
from garimpei.domain.monitoring.errors import ConfigurationSaveFailed
from garimpei.main import build_publish_exploration,build_read_monitoring_configuration,build_monitoring_handler
from garimpei.infra.queries.listing.exploration_source import ExplorationSource
from garimpei.infra.persistence.exploration_models import ExplorationOffer,ExplorationRevision
from garimpei.usecase.monitoring.save_step_usecase import StepInput
old=build_read_monitoring_configuration().execute()
new_name='Produto novo para corte MVCC'
held=Event();release=Event();second_started=Event();second_snapshot=Event();mutex=Lock()
seen=[];pids={}
original=ExplorationSource.snapshot

def snapshot(source,at):
 with mutex:index=len(seen);seen.append(source._configuration.execute())
 offers=original(source,at)
 if index==0:
  held.set()
  assert release.wait(8),'test did not release first publisher'
  assert source._configuration.execute()==old,'RR mixed parent and children after concurrent edit'
 else:
  second_snapshot.set()
 return offers

def publish(index):
 try:
  with connection.cursor() as cursor:cursor.execute('SELECT pg_backend_pid()');pids[index]=cursor.fetchone()[0]
  if index==1:second_started.set()
  return build_publish_exploration().execute()
 finally:connections.close_all()

def update():
 try:
  with connection.cursor() as cursor:cursor.execute("SET statement_timeout='500ms'")
  started=monotonic()
  try:
   build_monitoring_handler()._update.execute(StepInput('editar',old.revision,cep=old.cep,shipping_estimate=str(old.shipping_estimate or ''),resale_fee_percent='11.00',category_ids=old.category_ids,product_names=(*old.product_names,new_name)))
  except ConfigurationSaveFailed:
   return None,monotonic()-started
  current=build_read_monitoring_configuration().execute()
  from garimpei.main import build_first_alert_store,build_read_profit,_listing_clock
  from garimpei.config.env import load_listing_settings
  from garimpei.infra.persistence.listing_models import Listing
  from garimpei.infra.persistence.alert_models import FirstAlertIdentity
  listing=Listing.objects.get(external_id='16001');store=build_first_alert_store();now=_listing_clock(load_listing_settings())()
  store.publish(listing.id,store.prepare(listing.id),build_read_profit().execute(listing.id),now)
  assert FirstAlertIdentity.objects.get(listing=listing).decisions.latest('generation').financial['configuration_revision']==current.revision
  return current,monotonic()-started
 finally:connections.close_all()

def blockers(pid):
 with connection.cursor() as cursor:
  cursor.execute('SELECT pg_blocking_pids(%s)',[pid]);return cursor.fetchone()[0]

with patch.object(ExplorationSource,'snapshot',snapshot):
 with ThreadPoolExecutor(3) as pool:
  first=pool.submit(publish,0)
  try:
   assert held.wait(8),'publisher did not enter snapshot'
   writer=pool.submit(update)
   current,elapsed=writer.result(timeout=3)
   assert current is not None,('configuration writer blocked by F08 snapshot',elapsed)
   assert elapsed<1 and current.revision==old.revision+1
   assert current.resale_fee_percent==Decimal('11.00') and new_name in current.product_names
   second=pool.submit(publish,1);assert second_started.wait(3)
   deadline=monotonic()+2
   while monotonic()<deadline and pids[0] not in blockers(pids[1]):sleep(.01)
   assert pids[0] in blockers(pids[1]),'publisher session lock was not retained'
   assert not second_snapshot.is_set(),'second publisher entered before first committed'
  finally:release.set()
  first_id=first.result(timeout=5);second_id=second.result(timeout=5)
assert seen[0]==old and seen[1]==current
assert first_id!=second_id
assert ExplorationRevision.objects.get(id=first_id).sequence<ExplorationRevision.objects.get(id=second_id).sequence
first_payloads=ExplorationOffer.objects.filter(revision__id=first_id).values_list('payload',flat=True)
second_payloads=ExplorationOffer.objects.filter(revision__id=second_id).values_list('payload',flat=True)
assert first_payloads and second_payloads
assert all(p['composition']['configuration_revision']==old.revision and Decimal(p['composition']['fee_percent'])==old.resale_fee_percent for p in first_payloads)
assert all(p['composition']['configuration_revision']==current.revision and Decimal(p['composition']['fee_percent'])==current.resale_fee_percent for p in second_payloads)
assert build_read_monitoring_configuration().execute()==current
print('F08 RR: config writer and F16 publication committed while F08 held; old parent+children coherent; second publisher waited80808008; both revisions preserved; writer_seconds=',round(elapsed,4))
""",
            )
            assert not any(method == "POST" for method, _ in channel.calls)
        finally:
            resume_worker(group)


def test_snapshot_configuration_reader_requires_existing_consistent_transaction(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(tmp_path, enabled=False) as (instance, _, _, _):
        group = pause_worker(instance)
        try:
            _checked_shell(
                instance,
                """
from django.db import connection,transaction
from django.test.utils import CaptureQueriesContext
from garimpei.main import build_read_monitoring_configuration
from garimpei.domain.monitoring.errors import ConfigurationReadFailed
normal=build_read_monitoring_configuration()
with CaptureQueriesContext(connection) as queries:expected=normal.execute()
assert expected.configured and any('FOR UPDATE' in q['sql'] for q in queries)
reader=build_read_monitoring_configuration(repeatable_snapshot=True)
def refused():
 try:reader.execute()
 except ConfigurationReadFailed:return
 raise AssertionError('snapshot reader accepted an unsafe transaction')
refused()
with transaction.atomic():
 with connection.cursor() as cursor:cursor.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
 refused()
for isolation in ('REPEATABLE READ','SERIALIZABLE'):
 with transaction.atomic():
  with connection.cursor() as cursor:cursor.execute('SET TRANSACTION ISOLATION LEVEL '+isolation)
  with CaptureQueriesContext(connection) as queries:actual=reader.execute()
  assert actual==expected and not any('FOR UPDATE' in q['sql'] for q in queries)
assert normal.execute()==expected
print('Opt-in rejects autocommit/read committed; RR/serializable coherent without row lock; default reader retains FOR UPDATE')
""",
            )
        finally:
            resume_worker(group)


def test_exploration_projection_omits_unused_cycle_json_without_lazy_queries(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(tmp_path, enabled=False) as (instance, _, _, _):
        group = pause_worker(instance)
        try:
            _checked_shell(
                instance,
                """
from unittest.mock import patch
from django.db import connection,transaction
from django.db.models import QuerySet
from django.test.utils import CaptureQueriesContext
from garimpei.main import build_publish_exploration,_listing_clock
from garimpei.config.env import load_listing_settings
source=build_publish_exploration()._publisher._source
now=_listing_clock(load_listing_settings())()
def full_cycle_projection(query,*fields):return query
with transaction.atomic():
 with connection.cursor() as cursor:cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
 with CaptureQueriesContext(connection) as actual_queries:actual=source.snapshot(now)
 with patch.object(QuerySet,'defer',full_cycle_projection):
  with CaptureQueriesContext(connection) as baseline_queries:baseline=source.snapshot(now)
assert actual==baseline and len(actual)==6
assert len(actual_queries)==len(baseline_queries) and len(actual_queries)<=10
projection=' '.join(q['sql'].split(' FROM ',1)[0] for q in actual_queries if q['sql'].startswith('SELECT'))
for field in ('results','planned','diagnostics','window_evidence','origin'):
 assert '"runtime_collectioncycle"."'+field+'"' not in projection,field
assert not any('FROM "runtime_collectioncycle" WHERE' in q['sql'] for q in actual_queries)
print('F08 projection: five unused JSON fields absent; full Offer tuples identical; bounded same query count and no lazy cycle reloads',len(actual_queries))
""",
            )
        finally:
            resume_worker(group)
