import time
from pathlib import Path

from tests.factories.alert import WahaServer
from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.listing import ControlledClock
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import command, completed, shell, sql, wait_for


def target_messages(channel: WahaServer) -> list[dict[str, object]]:
    return [message for message in channel.messages if "/item/16001/" in str(message["body"])]


def wait_first(channel: WahaServer, clock: ControlledClock) -> None:
    next_advance = time.monotonic() + 6

    def confirmed() -> bool:
        nonlocal next_advance
        if time.monotonic() >= next_advance:
            clock.advance(6)
            next_advance = time.monotonic() + 6
        return len(target_messages(channel)) == 1

    wait_for(confirmed, "F16 first alert receipt", seconds=35)


def test_first_alert_enrichment_and_restart_keeps_one_receipt(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path, sample_ready=False) as (
        instance,
        source,
        clock,
        channel,
    ):
        assert not target_messages(channel)
        assert sql(
            instance, "SELECT count(*) FROM runtime_listingevent WHERE kind='discovered'"
        ) == [(0,)]
        shell(
            instance,
            "from garimpei.main import build_read_profit;from garimpei.infra.persistence.listing_models import Listing;l=Listing.objects.get(external_id='16001');assert build_read_profit().execute(l.id).resale.value is None",
        )
        source.rows["16006"]["description"] = "Funciona perfeitamente."
        source.rows["16001"]["description"] = "Usado. Funciona perfeitamente."
        clock.advance(61)
        completed(instance, 2)
        wait_first(channel, clock)
        assert "Preço de compra: R$ 1.000,00" in str(target_messages(channel)[0]["body"])
        assert "Preço de venda estimado: R$ 1.500,00" in str(target_messages(channel)[0]["body"])
        assert "Lucro estimado: R$ 350,00" in str(target_messages(channel)[0]["body"])
        assert target_messages(channel)[0]["to"] == "100@g.us"
        assert sql(
            instance, "SELECT count(*) FROM runtime_listingevent WHERE kind='discovered'"
        ) == [(0,)]
        shell(
            instance,
            """
from garimpei.main import build_read_alert_diagnostic
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import AlertIntent
l=Listing.objects.get(external_id='16001')
before=AlertIntent.objects.count()
d=build_read_alert_diagnostic().execute(l.id,l.latest_id)
assert d.state == 'confirmed' and d.confirmed_at is not None
assert d.matches_displayed_observation and d.first_alert_state == 'confirmed'
assert AlertIntent.objects.count()==before
""",
        )
        before = target_messages(channel)[0].copy()
        command(instance, "./scripts/stop.sh")
        clock.advance(6)
        command(instance, "./scripts/init.sh", "--disposable")
        shell(
            instance,
            """
from garimpei.main import build_alert_handler
for stage in ('adopt','refresh','reconcile','send'): build_alert_handler(stage).execute()
""",
        )
        assert target_messages(channel) == [before]
        shell(
            instance,
            """
from garimpei.main import build_read_alert_diagnostic,build_publish_exploration
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
l=Listing.objects.get(external_id='16001');r=FirstAlertIdentity.objects.get(listing=l)
d=build_read_alert_diagnostic().execute(l.id,l.latest_id)
assert d.intent_reference==r.intent_id and d.confirmed_at==r.intent.confirmed_at
assert r.intent.confirmed_message and r.intent.confirmed_ack and r.intent.recipient=='100@g.us'
build_publish_exploration().execute()
""",
        )
        identity = str(
            sql(instance, "SELECT id FROM runtime_listing WHERE external_id='16001'")[0][0]
        )
        status, _, html = instance.http(f"/ofertas/{identity}/")
        assert status == 200 and "Confirmada no servidor" in html
        assert "PlayStation 5" in html and "não comprova entrega ou leitura" in html
        assert target_messages(channel) == [before]


def test_manual_choice_is_consumed_but_later_input_can_alert(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, clock, channel):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                """
from garimpei.main import build_read_condition,build_classify_condition,build_alert_handler
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity, AlertIntent
l=Listing.objects.get(external_id='16001')
c=build_read_condition().execute(l.id)
build_classify_condition().execute(l.id,'good',c.state.revision)
for stage in ('adopt','refresh','send'): build_alert_handler(stage).execute()
r=FirstAlertIdentity.objects.get(listing=l)
assert r.reason == 'manual_change_only',r.reason
assert r.intent_id is None
assert not AlertIntent.objects.filter(first_decision__identity=r).exists()
""",
            )
        finally:
            resume_worker(group)
        assert not target_messages(channel)
        # Restart while the consumed manual input still blocks the first effect.
        command(instance, "./scripts/stop.sh")
        command(instance, "./scripts/init.sh", "--disposable")
        shell(
            instance,
            """
from garimpei.main import build_first_alert_store,build_read_profit,build_read_condition,_listing_clock
from garimpei.config.env import load_listing_settings
from garimpei.infra.persistence.listing_models import Listing,ManualCondition
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
l=Listing.objects.get(external_id='16001');now=_listing_clock(load_listing_settings())()
s=build_first_alert_store();s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l)
assert r.reason=='manual_change_only' and r.intent_id is None
assert ManualCondition.objects.get(listing=l).choice=='good'
assert build_read_condition().execute(l.id).state.effective=='good'
""",
        )
        assert not target_messages(channel)
        # A new observation with equivalent text does not bypass the consumed signature.
        clock.advance(61)
        completed(instance, 2)
        assert not target_messages(channel)
        source.rows["16001"]["description"] = "Usado. Funciona perfeitamente. Controle incluído."
        clock.advance(61)
        completed(instance, 3)
        wait_first(channel, clock)
        shell(
            instance,
            """
from garimpei.infra.persistence.listing_models import Listing,ManualCondition
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
l=Listing.objects.get(external_id='16001');r=FirstAlertIdentity.objects.get(listing=l)
assert ManualCondition.objects.get(listing=l).choice=='good'
assert r.intent.first_decision.cause=='automatic_input'
assert r.intent.first_decision.observation_id==l.latest_id
""",
        )


def test_publication_waits_and_final_check_blocks_expired_post(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, clock, channel):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                """
from datetime import timedelta
from garimpei.main import build_first_alert_store,build_read_profit,build_alert_store,build_alert_handler
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import AlertIntent,AlertFeedCursor
from garimpei.domain.alert.alert import Binding
from garimpei.config.env import load_listing_settings
from garimpei.main import _listing_clock
now=_listing_clock(load_listing_settings())()
l=Listing.objects.select_related('latest').get(external_id='16001')
s=build_first_alert_store(); s.adopt(now)
# The paused worker may not have ingested history when valuations become ready.
build_alert_handler('ingest').execute()
assert AlertFeedCursor.objects.get(installation='local').history_ready
for source,published,expected in ((None,None,'publication_missing'),(None,now,'publication_untrusted'),('fixture.published_at',now+timedelta(seconds=1),'publication_future'),('fixture.published_at',now-timedelta(hours=48,microseconds=1),'publication_expired')):
 e=dict(l.latest.evidence);e['published_at']=published.isoformat() if published else None;e['published_at_source']=source;e['description']='Funciona perfeitamente.';l.latest.evidence=e;l.latest.save()
 s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
 r=l.firstalertidentity_set.get();assert r.reason==expected,(r.reason,expected)
 assert not AlertIntent.objects.filter(first_decision__identity=r).exists()
e['published_at']=(now-timedelta(hours=48)).isoformat();e['published_at_source']='fixture.published_at';l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=l.firstalertidentity_set.get();assert r.intent_id is not None,r.reason
store=build_alert_store();delivery=store.claim(r.intent_id,Binding('synthetic','100@g.us','200@c.us'),now+timedelta(microseconds=1),reconcile=False)
assert delivery is None
r.intent.refresh_from_db();assert r.intent.reason=='publication_expired'
""",
            )
        finally:
            resume_worker(group)
        assert not target_messages(channel)


def test_missing_and_untrusted_dates_reach_diagnostic_then_valid_date_alerts(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, clock, channel):
        source.rows["16001"]["description"] = "Funciona perfeitamente."
        for cycle, raw, expected in (
            (2, None, "publication_missing"),
            (3, "há 2 horas", "publication_untrusted"),
        ):
            source.rows["16001"]["published_at"] = raw
            clock.advance(61)
            completed(instance, cycle)
            wait_for(
                lambda: (
                    sql(
                        instance,
                        "SELECT f.reason FROM runtime_firstalertidentity f JOIN runtime_listing l ON l.id=f.listing_id WHERE l.external_id='16001'",
                    )
                    == [(expected,)]
                ),
                expected,
                seconds=20,
            )
            assert not target_messages(channel)
            shell(
                instance,
                "from garimpei.main import build_read_alert_diagnostic; from garimpei.infra.persistence.listing_models import Listing; l=Listing.objects.get(external_id='16001'); d=build_read_alert_diagnostic().execute(l.id,l.latest_id); assert d.reason=="
                + repr(expected),
            )
        source.rows["16001"]["published_at"] = clock.value.isoformat()
        clock.advance(61)
        completed(instance, 4)
        wait_first(channel, clock)
        shell(
            instance,
            """
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
r=FirstAlertIdentity.objects.get(listing__external_id='16001')
assert r.intent.state=='confirmed'
assert set(r.decisions.values_list('publication_status',flat=True)) >= {'missing','untrusted','trusted'}
""",
        )


def test_channel_unavailable_queue_expires_with_wait_history(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, clock, channel):
        group = pause_worker(instance)
        try:
            from tests.integration.test_first_alert_review_regressions import PREPARE

            shell(
                instance,
                PREPARE
                + """
e['published_at']=(now-timedelta(hours=48)+timedelta(seconds=1)).isoformat();l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
""",
            )
            channel.ready = False
            shell(
                instance,
                """
from garimpei.main import build_alert_handler
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
build_alert_handler('send').execute()
r=FirstAlertIdentity.objects.get(listing__external_id='16001')
assert r.intent.state=='blocked' and r.intent.reason=='session_unavailable'
assert r.decisions.filter(reason='eligible').exists()
""",
            )
            channel.ready = True
            clock.advance(61)
            shell(
                instance,
                """
from garimpei.main import build_alert_handler,build_read_alert_diagnostic
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
build_alert_handler('send').execute();build_alert_handler('refresh').execute()
l=Listing.objects.get(external_id='16001');r=FirstAlertIdentity.objects.get(listing=l)
d=build_read_alert_diagnostic().execute(l.id,l.latest_id)
assert r.intent.state=='cancelled' and r.intent.reason=='publication_expired'
assert r.intent.failures==1 and r.intent.attempts.count()==0
assert d.current_reason=='publication_expired' and d.first_alert_state=='cancelled'
assert any(history.state=='cancelled' for history in d.history)
assert r.decisions.filter(reason='eligible').exists() and r.decisions.filter(reason='publication_expired').exists()
""",
            )
            assert not any(method == "POST" for method, _ in channel.calls)
        finally:
            resume_worker(group)
