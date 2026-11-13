"""Real PostgreSQL authorization, event query, synthetic WAHA and legacy compatibility."""

from datetime import datetime, timedelta
from pathlib import Path

from tests.factories.alert_scenario import alert_scenario, alert_shell, pause_worker, resume_worker
from tests.factories.listing import ControlledClock
from tests.factories.runtime import FoundationInstance
from tests.factories.valuation import listing
from tests.integration.test_collection import completed, sql, wait_for


def _reach_unsent_financial_boundary(
    instance: FoundationInstance, clock: ControlledClock, keys: tuple[str, ...]
) -> None:
    """A paused worker may have scheduled a channel wait before the explicit client."""
    identities = ",".join("'" + str(int(key)) + "'" for key in keys)
    rows = sql(
        instance,
        "SELECT a.next_action,a.state,a.reason,a.body,a.lease_until,"
        "(SELECT count(*) FROM runtime_alertattempt t WHERE t.intent_id=a.id) "
        "FROM runtime_alertintent a "
        "LEFT JOIN runtime_alerteventdecision d ON a.decision_id=d.id "
        "LEFT JOIN runtime_listingevent e ON d.event_id=e.id "
        "LEFT JOIN runtime_firsteligibilitydecision f ON a.first_decision_id=f.id "
        "LEFT JOIN runtime_firstalertidentity i ON f.identity_id=i.id "
        "JOIN runtime_listing l ON COALESCE(e.listing_id,i.listing_id)=l.id "
        "WHERE l.external_id IN (" + identities + ") "
        "AND a.state IN ('queued','blocked')",
    )
    deadline = clock.value
    for due, state, reason, body, lease, attempts in rows:
        assert isinstance(due, datetime)
        assert not body and lease is None and attempts == 0
        assert state == "queued" or reason == "configuration_missing"
        assert due <= clock.value + timedelta(seconds=300)
        deadline = max(deadline, due)
    clock.value = deadline
    clock.advance(0)


def test_financial_authorization_freezes_same_event_and_preserves_legacy(tmp_path: Path) -> None:
    with alert_scenario(tmp_path, enabled=False) as (instance, source, clock, channel):
        clock.advance(1)
        for n in range(951, 957):
            source.rows[str(n)] = listing(
                str(n),
                "1000,00",
                published_at=clock.value.isoformat(),
                condition="Funciona bem",
                pickup=False,
                delivery=True,
                delivery_cep="01001000",
            )
        clock.advance(61)
        completed(instance, 2)
        wait_for(
            lambda: (
                sql(
                    instance,
                    "SELECT count(*) FROM runtime_valuationprogress p JOIN runtime_listing l ON p.listing_id=l.id WHERE l.external_id IN ('951','952','953','954','955','956') AND p.current_id IS NOT NULL",
                )
                == [(6,)]
            ),
            "six financial evaluations",
            seconds=45,
        )
        group = pause_worker(instance)
        try:
            alert_shell(
                instance,
                """
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from django.db import connections
from garimpei.main import build_read_listing_changes
from garimpei.domain.alert.financial_snapshot import FORMAT
from garimpei.infra.repository.alert.financial import decode_snapshot
store.ingest(build_read_listing_changes().execute(),clock())
for key in ('951','952','953','954','955','956'):
    prepare_first(key)
# This test supplies a binding directly. Make authorization due independently
# of channel-configuration backoff recorded before the worker was paused.
AlertIntent.objects.filter(first_decision__identity__listing__external_id__in=(
    '951','952','953','954','955','956'
)).update(next_action=clock())
# A failure before transaction commit leaves no partial body/snapshot/attempt.
from unittest.mock import patch
row=intent('951')
with patch.object(AlertAttempt.objects,'create',side_effect=RuntimeError('controlled authorization rollback')):
    try: store.claim(row.id,binding,clock(),reconcile=False)
    except RuntimeError: pass
    else: raise AssertionError('rollback fault not exercised')
row.refresh_from_db()
assert row.body=='' and row.financial=={} and row.body_format=='' and not row.attempts.exists()
# Independent connections race for one authorization.
def claim(_):
    try:return build_alert_store().claim(row.id,binding,clock(),reconcile=False)
    finally:connections.close_all()
with ThreadPoolExecutor(max_workers=2) as pool: deliveries=list(pool.map(claim,range(2)))
assert sum(d is not None for d in deliveries)==1
first=next(d for d in deliveries if d)
row.refresh_from_db()
frozen=dict(row.financial);body=row.body
assert row.body_format==FORMAT and decode_snapshot(frozen) is not None
assert frozen['event_id'] is None and frozen['schema_version']==2
assert frozen['observation_id']==str(row.first_decision.observation_id)
assert body.index('Preço de compra:')<body.index('Preço de venda estimado:')<body.index('*Lucro estimado:')
assert 'frete' not in body.lower() and 'transporte' not in body.lower()
# Use the actual synthetic WAHA gateway to transmit once, then reconcile a lost response.
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.main import _effective_alert_settings,_alert_policy
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
assert gateway.check(binding)
outcome=gateway.send(first)
store.finish(first,Outcome('uncertain','controlled lost response'),clock())
# A subsequent calculation/configuration cannot change the authorized record.
d=row.first_decision;d.financial={};d.save(update_fields=['financial'])
later=clock()+timedelta(seconds=61)
recovery=store.claim(row.id,binding,later,reconcile=True)
assert recovery and recovery.body==body
store.finish(recovery,gateway.reconcile(recovery,later),later)
row.refresh_from_db()
assert row.financial==frozen and row.body==body and row.state=='confirmed'
assert row.attempts.count()==1
# A genuine previously authorized legacy body keeps its original attempt and binding.
legacy=intent('952')
legacy.first_decision=None;legacy.decision=decision('952')
legacy.body='CORPO LEGADO EXATO sem venda';legacy.session=binding.session;legacy.recipient=binding.recipient;legacy.account=binding.account
legacy.state='uncertain';legacy.save()
legacy.decision.financial={};legacy.decision.save(update_fields=['financial'])
AlertAttempt.objects.create(intent=legacy,ordinal=1,generation=1,authorized_at=clock())
old=store.claim(legacy.id,binding,later,reconcile=True)
assert old and old.body=='CORPO LEGADO EXATO sem venda'
legacy.refresh_from_db();assert legacy.financial=={} and legacy.body_format==''
store.finish(old,Outcome('uncertain','original transmission unknown'),later)
again=store.claim(legacy.id,binding,later+timedelta(seconds=61),reconcile=True)
assert again and again.body==old.body and again.reference==old.reference
assert legacy.attempts.count()==1
# Unauthorised legacy intent is re-evaluated by the same normal event-composition query.
legacy=intent('953');identity=legacy.id
legacy.first_decision.financial={'purchase':'1000','profit':'100'};legacy.first_decision.save(update_fields=['financial'])
assert store.claim(identity,binding,clock(),reconcile=False) is None
assert intent('953').state=='blocked' and intent('953').reason=='profit_pending'
prepare_first('953',later)
new=store.claim(identity,binding,later,reconcile=False)
assert new and intent('953').id==identity and intent('953').body_format==FORMAT
# Possibly transmitted intent without its body is kept for review, never reconstructed.
missing=intent('954')
AlertAttempt.objects.create(intent=missing,ordinal=1,generation=1,authorized_at=clock())
missing.state='uncertain';missing.save()
assert store.claim(missing.id,binding,later,reconcile=True) is None
assert intent('954').state=='review' and intent('954').reason=='authorized_body_missing'
assert intent('954').body=='' and intent('954').attempts.count()==1
# Complete but incompatible data cannot authorize a new message.
wrong=intent('955');raw=dict(wrong.first_decision.financial);raw['observation_id']=str(target('956').latest_id)
wrong.first_decision.financial=raw;wrong.first_decision.save(update_fields=['financial'])
assert store.claim(wrong.id,binding,clock(),reconcile=False) is None
assert intent('955').reason=='profit_observation_mismatch' and not intent('955').attempts.exists()
# An evaluation reference/revision from another snapshot cannot authorize coherent-looking money.
wrong=intent('956');raw=dict(wrong.first_decision.financial);raw['evaluation_revision']=999
wrong.first_decision.financial=raw;wrong.first_decision.save(update_fields=['financial'])
assert store.claim(wrong.id,binding,clock(),reconcile=False) is None
assert intent('956').reason=='profit_incompatible' and not intent('956').attempts.exists()

print('F20 rollback/concurrent authorization/frozen snapshot/WAHA reconciliation/legacy/incomplete/incompatible/missing-body PASS')
""",
            )
        finally:
            resume_worker(group)
        assert len([c for c in channel.calls if c[0] == "POST"]) == 1


def test_worker_trio_exact_brl_values_and_reduction_uses_event_before_later_price(
    tmp_path: Path,
) -> None:
    from tests.factories.alert import WahaServer, serve_waha
    from tests.factories.exploration import prepare_exploration_instance
    from tests.factories.financial_presentation_lab import FinancialSource, publish_and_check
    from tests.factories.listing import serve
    from tests.integration.test_collection import command, shell

    source, channel = FinancialSource(), WahaServer()
    with serve(source) as origin, serve_waha(channel) as waha:
        instance, clock = prepare_exploration_instance(
            Path(__file__).resolve().parents[4], tmp_path, origin
        )
        with instance.private_file.open("a") as out:
            out.write(
                f"GARIMPEI_ALERTS_ENABLED=false\nGARIMPEI_ALERT_FIXTURE_URL={waha}\nGARIMPEI_WAHA_SESSION=synthetic\nGARIMPEI_WAHA_RECIPIENT=100@c.us\nGARIMPEI_WAHA_ACCOUNT=200@c.us\n"
            )
        command(instance, "./scripts/init.sh", "--disposable")
        try:
            shell(
                instance,
                "from tests.factories.financial_presentation_lab import configure_financial; configure_financial()",
            )
            completed(instance, 1)
            publish_and_check(instance)
            clock.advance(1)
            for n, price in [(10951, "1000"), (10952, "1350"), (10953, "1400"), (10954, "1200")]:
                source.rows[str(n)] = listing(
                    str(n),
                    price + ",00",
                    title="PS5 Slim Digital 825GB",
                    condition="Funciona bem",
                    published_at=clock.value.isoformat(),
                    pickup=True,
                    delivery=False,
                )
            clock.advance(61)
            completed(instance, 2)
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT count(*) FROM runtime_valuationprogress p JOIN runtime_listing l ON p.listing_id=l.id WHERE l.external_id IN ('10951','10952','10953','10954') AND p.current_id IS NOT NULL",
                    )
                    == [(4,)]
                ),
                "exact monetary inputs",
                seconds=45,
            )
            group = pause_worker(instance)
            try:
                _reach_unsent_financial_boundary(
                    instance, clock, ("10951", "10952", "10953", "10954")
                )
                alert_shell(
                    instance,
                    """
from garimpei.main import build_read_listing_changes,_effective_alert_settings,_alert_policy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
store.ingest(build_read_listing_changes().execute(),clock())
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
for key,expected in [('10951','350.00'),('10952','0.00'),('10953','-50.00'),('10954','150.00')]:
 p=build_read_profit().execute(target(key).id,event=False)
 assert p.resale.value==Decimal('1500') and p.profit.value==Decimal(expected)
 prepare_first(key)
 delivery=store.claim(intent(key).id,binding,clock(),reconcile=False)
 assert delivery
 store.finish(delivery,gateway.send(delivery),clock())
 row=intent(key)
 assert row.state=='confirmed' and row.financial['resale']=='1500.00' and Decimal(row.financial['profit'])==Decimal(expected)
 assert '*Lucro estimado:' in row.body
print('WRK-MENSAGEM-01/08 exact positive, zero and negative confirmed by synthetic WAHA PASS')
""",
                )
            finally:
                resume_worker(group)
            for count, price in [(3, "1000"), (4, "900")]:
                source.rows["10954"]["price"] = "R$ " + price + ",00"
                clock.advance(61)
                completed(instance, count)
            group = pause_worker(instance)
            try:
                alert_shell(
                    instance,
                    """
from garimpei.main import build_read_listing_changes,_effective_alert_settings,_alert_policy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
store.ingest(build_read_listing_changes().execute(),clock())
event=ListingEvent.objects.get(listing=target('10954'),kind='price_decreased',observation__price=1000)
p=build_read_profit().execute(event.id,event=True)
assert p.purchase.value==1000 and target('10954').latest.price==900
store.evaluate(event.id,p,clock())
row=AlertIntent.objects.get(decision__event=event)
# Exercise the valid worker ordering that can happen before this test pauses it.
from garimpei.usecase.alert.send_alert_usecase import SendAlertUseCase
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
SendAlertUseCase(store,gateway,None,build_read_listing_changes(),clock).execute()
row.refresh_from_db()
assert row.state=='blocked' and row.reason=='configuration_missing'
assert not row.body and row.lease_until is None and row.attempts.count()==0
assert clock()<row.next_action<=clock()+timedelta(seconds=_alert_policy().retry_max)
assert store.claim(row.id,binding,clock(),reconcile=False) is None
""",
                )
                _reach_unsent_financial_boundary(instance, clock, ("10954",))
                alert_shell(
                    instance,
                    """
from garimpei.main import _effective_alert_settings,_alert_policy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
event=ListingEvent.objects.get(listing=target('10954'),kind='price_decreased',observation__price=1000)
p=build_read_profit().execute(event.id,event=True)
assert p.purchase.value==1000 and target('10954').latest.price==900
row=AlertIntent.objects.get(decision__event=event)
assert row.next_action<=clock()
delivery=store.claim(row.id,binding,clock(),reconcile=False);assert delivery
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
store.finish(delivery,gateway.send(delivery),clock());row.refresh_from_db()
assert row.state=='confirmed'
assert Decimal(row.financial['purchase'])==1000 and Decimal(row.financial['resale'])==1500 and Decimal(row.financial['profit'])==350
assert 'Preço de compra: R$ 1.000,00' in row.body and 'Preço anterior: R$ 1.200,00' in row.body
assert 'R$ 900,00' not in row.body
# Change the actual persisted fee, then collect a separately identified fractional case.
from garimpei.main import build_read_monitoring_configuration,build_monitoring_handler
from garimpei.usecase.monitoring.save_step_usecase import StepInput
config=build_read_monitoring_configuration().execute()
build_monitoring_handler()._update.execute(StepInput('editar',config.revision,cep=config.cep,resale_fee_percent='12.50',category_ids=config.category_ids,product_names=config.product_names))
print('WRK-MENSAGEM-02 event 1000 remains frozen after observation 900 PASS')
""",
                )
            finally:
                resume_worker(group)
            clock.advance(1)
            source.rows["10955"] = listing(
                "10955",
                "70,00",
                title="iPhone 13 128GB",
                condition="Funciona bem",
                description="Funcionando perfeitamente.",
                published_at=clock.value.isoformat(),
                pickup=True,
                delivery=False,
            )
            clock.advance(61)
            completed(instance, 5)
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT count(*) FROM runtime_valuationprogress p JOIN runtime_listing l ON p.listing_id=l.id WHERE l.external_id='10955' AND p.current_id IS NOT NULL",
                    )
                    == [(1,)]
                ),
                "fraction evaluation",
                seconds=45,
            )
            group = pause_worker(instance)
            try:
                _reach_unsent_financial_boundary(instance, clock, ("10955",))
                alert_shell(
                    instance,
                    """
from garimpei.main import build_read_listing_changes,_effective_alert_settings,_alert_policy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
store.ingest(build_read_listing_changes().execute(),clock())
p=build_read_profit().execute(target('10955').id,event=False)
assert p.purchase.value==70 and p.resale.value==101 and p.fee_percent==Decimal('12.50') and p.fee.value==Decimal('12.63') and p.profit.value==Decimal('18.37')
prepare_first('10955')
delivery=store.claim(intent('10955').id,binding,clock(),reconcile=False);assert delivery
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
store.finish(delivery,gateway.send(delivery),clock());row=intent('10955')
assert row.state=='confirmed' and 'R$ 18,37' in row.body and row.financial['fee']=='12.63'
print('WRK-MENSAGEM-08 actual F07 fraction -> snapshot -> synthetic WAHA PASS')
""",
                )
            finally:
                resume_worker(group)
            assert len([c for c in channel.calls if c[0] == "POST"]) == 6
        finally:
            command(instance, "./scripts/stop.sh", "--clean")


def test_additive_migration_keeps_authorized_legacy_and_event_history(tmp_path: Path) -> None:
    from tests.factories.alert_scenario import add_cases

    with alert_scenario(tmp_path, enabled=False) as (instance, source, clock, channel):
        add_cases(source, clock)
        clock.advance(61)
        completed(instance, 2)
        wait_for(
            lambda: (
                sql(
                    instance,
                    "SELECT count(*) FROM runtime_valuationprogress p JOIN runtime_listing l ON p.listing_id=l.id WHERE l.external_id='903' AND p.current_id IS NOT NULL",
                )
                == [(1,)]
            ),
            "legacy valuation",
            seconds=40,
        )
        group = pause_worker(instance)
        try:
            alert_shell(
                instance,
                """
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from garimpei.main import build_read_listing_changes
store.ingest(build_read_listing_changes().execute(),clock())
prepare_first()
row=intent()
FirstAlertIdentity.objects.update(intent=None)
AlertIntent.objects.exclude(id=row.id).filter(attempts__isnull=True).delete()
row.first_decision=None;row.decision=decision();row.save()
row.body='CORPO LEGADO EXATO\\nsem venda estimada'
row.session,row.recipient,row.account=binding.session,binding.recipient,binding.account
row.state='uncertain';row.save()
attempt=AlertAttempt.objects.create(intent=row,ordinal=1,generation=1,authorized_at=clock(),message_id='legacy-message')
before=(str(row.id),str(row.decision.event.id),row.body,row.recipient,ListingEvent.objects.count(),AlertIntent.objects.count(),AlertAttempt.objects.count())
# Exercise applying F20 to an actual database containing the pre-F20 schema and body.
MigrationExecutor(connection).migrate([('runtime','0012_opportunity_collection')])
with connection.cursor() as c:
 c.execute('SELECT body FROM runtime_alertintent WHERE id=%s',[row.id]);assert c.fetchone()[0]==before[2]
MigrationExecutor(connection).migrate([('runtime','0013_alert_message_snapshot')])
executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
row.refresh_from_db()
after=(str(row.id),str(row.decision.event.id),row.body,row.recipient,ListingEvent.objects.count(),AlertIntent.objects.count(),AlertAttempt.objects.count())
assert after==before and row.financial=={} and row.body_format==''
assert row.attempts.get().message_id=='legacy-message'
recovery=store.claim(row.id,binding,clock()+timedelta(seconds=61),reconcile=True)
assert recovery and recovery.body==before[2]
assert row.attempts.count()==1
print('E2E-MENSAGEM-02 old schema -> additive migration preserves body, intent, event, recipient and attempt PASS')
""",
            )
        finally:
            resume_worker(group)
        assert not channel.messages
