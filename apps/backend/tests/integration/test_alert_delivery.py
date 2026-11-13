from pathlib import Path

import pytest

from tests.factories.alert_scenario import (
    add_cases,
    alert_scenario,
    alert_shell,
    pause_worker,
    resume_worker,
)
from tests.factories.operations_metrics import InstanceMeasurements, workload_signature
from tests.integration.test_collection import completed, sql, wait_for


def test_durable_attempts_rollback_history_and_generations(tmp_path: Path) -> None:
    with alert_scenario(tmp_path, enabled=False) as (instance, source, clock, channel):
        add_cases(source, clock)
        clock.advance(61)
        completed(instance, 2)
        source.rows["903"]["price"] = "R$ 2.299,99"
        clock.advance(61)
        completed(instance, 3)
        wait_for(
            lambda: (
                sql(
                    instance,
                    "SELECT count(*) FROM runtime_listingevent e JOIN runtime_listing l ON e.listing_id=l.id WHERE l.external_id='903'",
                )
                == [(2,)]
            ),
            "discovery published",
        )
        wait_for(
            lambda: (
                sql(
                    instance,
                    "SELECT count(*) FROM runtime_valuationprogress p JOIN runtime_listing l ON p.listing_id=l.id WHERE l.external_id IN ('901','902','903') AND p.current_id IS NOT NULL",
                )
                == [(3,)]
            ),
            "new valuations published",
            seconds=35,
        )
        group = pause_worker(instance)
        try:
            alert_shell(
                instance,
                """
from unittest.mock import patch
from dataclasses import replace
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from garimpei.domain.listing.read_models import ChangePage
from garimpei.main import build_read_listing_changes
# Cursor and decision are one transaction even when a failure occurs mid-page.
AlertFeedCursor.objects.all().delete()
FirstAlertIdentity.objects.update(intent=None)
AlertIntent.objects.all().delete()
FirstEligibilityDecision.objects.all().delete()
FirstAlertIdentity.objects.all().delete()
FirstAlertInventory.objects.update(completed=False,cursor=None)
AlertEventDecision.objects.all().delete()
page=build_read_listing_changes().execute()
original=store._accept
calls=0
def fail_second(identity,now):
    global calls
    calls+=1
    if calls==2: raise RuntimeError('controlled rollback')
    original(identity,now)
try:
    with patch.object(store,'_accept',side_effect=fail_second):store.ingest(page,clock())
except RuntimeError:pass
else:raise AssertionError('fault did not occur')
assert not AlertFeedCursor.objects.exists() and not AlertEventDecision.objects.exists()
store.ingest(page,clock());store.ingest(page,clock())
assert AlertEventDecision.objects.count()==len(page.events)
assert store.cursor()==page.cursor
print('WRK-RETOMADA-03 PASS')
# A wrong observation never supplies the financial calculation.
p=build_read_profit().execute(target().id,event=False)
assert p.profit.value is not None
first_store=build_first_alert_store();first_store.adopt(clock())
signature=first_store.prepare(target().id)
first_store.publish(target().id,signature,replace(p,observation_id=target('901').latest_id),clock())
assert first_decision().state=='waiting' and first_decision().reason=='profit_observation_mismatch'
assert first_state().intent_id is None
first_store.publish(target().id,signature,None,clock())
assert first_decision().state=='waiting'
first_store.publish(target().id,signature,p,clock())
assert intent().first_decision.financial['observation_id']==str(p.observation_id)
print('WRK-ELEGIBILIDADE-03/08 current composition PASS')
reduction=ListingEvent.objects.get(listing=target(),kind='price_decreased')
reduction_profit=build_read_profit().execute(reduction.id,event=True)
store.evaluate(reduction.id,reduction_profit,clock())
assert AlertEventDecision.objects.get(event=reduction).reason=='first_alert_causal_event'
assert not AlertIntent.objects.filter(decision__event=reduction).exists()

# History failure prevents authorizations until ingestion restores it.
store.pause()
assert store.claim(intent().id,binding,clock(),reconcile=False) is None
assert not AlertAttempt.objects.exists()
store.ingest(ChangePage((),store.cursor()),clock())
# Configuration wait has a durable, sanitized reason and no authorized attempt.
store.block(intent().id,'session_unavailable',clock())
assert intent().state=='blocked' and not AlertAttempt.objects.exists()
AlertIntent.objects.filter(id=intent().id).update(next_action=clock())
first=store.claim(intent().id,binding,clock(),reconcile=False)
assert first and AlertAttempt.objects.count()==1
assert store.claim(intent().id,binding,clock(),reconcile=False) is None
# A proven pre-connect failure can retry with the exact same body/reference.
store.finish(first,Outcome('safe_retry','not_transmitted'),clock())
assert intent().state=='safe_retry'
retry_at=intent().next_action
second=store.claim(intent().id,binding,retry_at,reconcile=False)
assert second and first.reference==second.reference and first.body==second.body
assert AlertAttempt.objects.count()==2
assert store.claim(intent().id,binding,retry_at,reconcile=False) is None
print('WRK-ENVIO-01/02; WRK-RETOMADA-02 PASS')
# A crash after authorization is only reclaimed as reconciliation, never another POST.
recovered_at=retry_at+timedelta(seconds=61)
recovered=store.claim(intent().id,binding,recovered_at,reconcile=True)
assert recovered and recovered.reconcile and recovered.generation>second.generation
assert AlertAttempt.objects.count()==2
assert store.claim(intent().id,binding,recovered_at,reconcile=False) is None
store.finish(second,Outcome('confirmed','late',Receipt('old',True,binding.recipient,second.body,2)),recovered_at)
assert intent().state=='uncertain' and intent().confirmed_at is None
# A changed configuration still reconciles the original immutable binding.
changed=store.claim(intent().id,replace(binding,recipient='300@c.us'),recovered_at+timedelta(seconds=61),reconcile=True)
assert changed and changed.binding==binding and intent().recipient==binding.recipient
resume_at=recovered_at+timedelta(seconds=122)
recovery=store.claim(intent().id,binding,resume_at,reconcile=True)
assert recovery
from garimpei.usecase.alert.reconcile_alert_usecase import ReconcileAlertUseCase
from tests.factories.alert import UnavailableSessionGateway
ReconcileAlertUseCase(store,UnavailableSessionGateway(),binding,lambda:resume_at+timedelta(days=1)).execute()
assert intent().state=='review' and intent().confirmed_at is None
assert not store.ready(resume_at+timedelta(days=2),reconcile=True)
assert AlertAttempt.objects.count()==2
print('WRK-ENVIO-05/06/07 PASS')
store.evaluate(reduction.id,reduction_profit,resume_at+timedelta(days=1))
assert AlertEventDecision.objects.get(event=reduction).reason=='first_alert_causal_event'
assert AlertEventDecision.objects.get(event=reduction).state=='excluded'
print('WRK-ELEGIBILIDADE-09 PASS')
# Two independent ORM connections race for the same intent; only one authorizes.
from concurrent.futures import ThreadPoolExecutor
from django.db import connections
prepare_first('901')
AlertIntent.objects.filter(id=intent('901').id).update(next_action=clock())
def race_claim(_):
    try:return build_alert_store().claim(intent('901').id,binding,clock(),reconcile=False)
    finally:connections.close_all()
with ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(race_claim,range(2)))
assert sum(result is not None for result in results)==1
assert AlertAttempt.objects.filter(intent=intent('901')).count()==1
print('LEASE-CONCURRENCY two connections PASS')
# A reader evaluating a dependent event must not mix pre/post confirmation history.
from threading import Thread,Event
from django.db import connection
from garimpei.infra.persistence.monitoring_unit_of_work import lock_monitoring_publication
from time import monotonic,sleep
candidate=next(result for result in results if result is not None)
started,finished=Event(),Event()
backend=[]
def confirm_from_other_connection():
    try:
        connection.ensure_connection()
        backend.append(connection.connection.info.backend_pid)
        started.set()
        build_alert_store().finish(candidate,Outcome('confirmed','ack',Receipt('concurrent-ack',True,binding.recipient,candidate.body,1)),clock())
        finished.set()
    finally:connections.close_all()
with transaction.atomic():
    lock_monitoring_publication()
    assert not AlertIntent.objects.filter(id=candidate.reference,state='confirmed').exists()
    publisher=Thread(target=confirm_from_other_connection)
    publisher.start()
    assert started.wait(3)
    deadline=monotonic()+3
    waiting=False
    while not finished.is_set() and monotonic()<deadline:
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_stat_clear_snapshot()')
            cursor.execute('SELECT wait_event FROM pg_stat_activity WHERE pid=%s',[backend[0]])
            observed=cursor.fetchone()
            waiting=observed is not None and observed[0]=='advisory'
        if waiting:break
        sleep(.01)
    assert waiting and not finished.is_set(), 'confirmation crossed an active dependency snapshot'
    assert AlertIntent.objects.filter(id=candidate.reference,state='authorized').exists()
publisher.join(3)
assert finished.is_set() and intent('901').state=='confirmed'
print('CONFIRMATION-CONCURRENCY consistent dependency history PASS')


""",
            )
        finally:
            resume_worker(group)
        assert not channel.messages


@pytest.mark.parametrize("kill_worker", [False, True], ids=["control", "fault"])
def test_killed_worker_reconciles_authorized_post_and_continues_new_deliveries(
    tmp_path: Path,
    kill_worker: bool,
) -> None:
    _run_post_boundary(tmp_path, kill_worker, "confirmed")


def test_killed_worker_reconciles_lost_post_response(tmp_path: Path) -> None:
    _run_post_boundary(tmp_path, True, "lost")


def _run_post_boundary(tmp_path: Path, kill_worker: bool, channel_mode: str) -> None:
    import os
    import signal

    from garimpei.infra.runtime.processes import verify_process
    from tests.factories.alert_scenario import wait_alerts
    from tests.factories.valuation import listing
    from tests.integration.test_collection import command, wait_for

    with alert_scenario(tmp_path) as (instance, source, clock, channel):
        with InstanceMeasurements(
            instance,
            tmp_path / "post-measurements.json",
            mode="fault" if kill_worker else "control",
        ) as measurements:
            channel.mode = channel_mode
            channel.hold_post = True
            clock.advance(1)
            source.rows["931"] = listing(
                "931",
                "1000,00",
                published_at=clock.value.isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            clock.advance(61)
            completed(instance, 2)
            assert channel.held.wait(35), "worker did not reach held POST"
            original = sql(
                instance, "SELECT id::text FROM runtime_alertintent WHERE state='authorized'"
            )
            assert len(original) == 1 and len(channel.messages) == 1
            clock.advance(61)
            if kill_worker:
                owner = next(
                    record
                    for record in instance.manifest["processes"]
                    if "runworker" in record["command"]
                )
                verify_process(owner, instance.config.root)
                os.killpg(owner["pgid"], signal.SIGKILL)
            channel.release.set()
            if kill_worker:
                command(instance, "./scripts/stop.sh")
                command(instance, "./scripts/init.sh", "--disposable")
            wait_alerts(instance, 1, clock)
            assert (
                sql(instance, "SELECT id::text FROM runtime_alertintent WHERE state='confirmed'")
                == original
            )
            assert sql(instance, "SELECT count(*) FROM runtime_alertattempt") == [(1,)]
            assert len([call for call in channel.calls if call[0] == "POST"]) == 1
            # The next input belongs to a new source snapshot, not an already
            # admitted collection whose window predates the input after restart.
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT c.finished_at IS NOT NULL AND s.next_attempt_at > '"
                        + clock.value.isoformat()
                        + "'::timestamptz FROM runtime_collectionstate s "
                        "JOIN runtime_collectioncycle c ON c.id=s.current_id",
                    )
                    == [(True,)]
                ),
                "collection checkpoint before the next source input",
                seconds=35,
            )
            # A technical send job may remain doing; a later business tick still progresses.
            channel.mode, channel.hold_post = "confirmed", False
            clock.advance(1)
            source.rows["932"] = listing(
                "932",
                "1000,00",
                published_at=clock.value.isoformat(),
                delivery=True,
                delivery_cep="01001000",
                pickup=False,
            )
            clock.advance(61)
            wait_alerts(instance, 2, clock)
            assert len([call for call in channel.calls if call[0] == "POST"]) == 2
            measurements.observed.update(
                offers=2,
                confirmed_posts=len(channel.messages),
                workload_signature=workload_signature(source.rows),
            )
