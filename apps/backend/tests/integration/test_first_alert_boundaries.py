from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_cases, first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


@pytest.mark.parametrize(
    "case",
    [
        "inventory_barrier",
        "concurrent",
        "zero",
        "negative",
        "manual_race",
        "manual_defect",
        "stale_observation",
        "history_unavailable",
        "oscillation",
    ],
)
def test_first_alert_publication_boundaries(tmp_path: Path, case: str) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, channel):
        group = pause_worker(instance)
        try:
            scripts = {
                "inventory_barrier": """
from garimpei.main import _effective_alert_settings,_alert_policy,build_read_listing_changes
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.usecase.alert.refresh_first_eligibility_usecase import RefreshFirstEligibilityUseCase
from garimpei.usecase.alert.send_alert_usecase import SendAlertUseCase
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l);assert r.intent.state=='queued' and r.intent.first_decision.financial['schema_version']==2
FirstAlertInventory.objects.update(completed=False,cursor=l.id)
RefreshFirstEligibilityUseCase(s,build_read_profit(),lambda:now).execute()
assert store.claim(r.intent_id,binding,now,reconcile=False) is None
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
SendAlertUseCase(store,gateway,binding,build_read_listing_changes(),lambda:now).execute()
r.intent.refresh_from_db();assert r.intent.state=='queued' and r.intent.attempts.count()==0
s.adopt(now);assert FirstAlertInventory.objects.get().completed
assert store.claim(r.intent_id,binding,now,reconcile=False) is not None
""",
                "concurrent": """
from concurrent.futures import ThreadPoolExecutor
from django.db import close_old_connections
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l)
def claim(_):
 try:return build_alert_store().claim(r.intent_id,binding,now,reconcile=False)
 finally:close_old_connections()
with ThreadPoolExecutor(max_workers=2) as pool: deliveries=list(pool.map(claim,range(2)))
assert sum(d is not None for d in deliveries)==1
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r.refresh_from_db();assert AlertIntent.objects.filter(first_decision__identity=r).count()==1
from garimpei.main import _effective_alert_settings,_alert_policy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
delivery=next(d for d in deliveries if d is not None)
store.finish(delivery,gateway.send(delivery),now)
assert AlertIntent.objects.get(id=delivery.reference).state=='confirmed'
""",
                "zero": """
from decimal import Decimal
e['price']='1350.00';l.latest.price=Decimal('1350.00');l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l);delivery=store.claim(r.intent_id,binding,now,reconcile=False)
assert delivery is not None and 'Lucro estimado: R$ 0,00' in delivery.body
""",
                "negative": """
from decimal import Decimal
e['price']='1400.00';l.latest.price=Decimal('1400.00');l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l);delivery=store.claim(r.intent_id,binding,now,reconcile=False)
assert delivery is not None and 'Lucro estimado: -R$ 50,00' in delivery.body
""",
                "manual_race": """
from garimpei.main import build_classify_condition,build_read_condition
e['description']='Não foi testado.';l.latest.evidence=e;l.latest.save()
signature=s.prepare(l.id);profit=build_read_profit().execute(l.id)
condition=build_read_condition().execute(l.id)
build_classify_condition().execute(l.id,'good',condition.state.revision)
s.publish(l.id,signature,profit,now)
r=FirstAlertIdentity.objects.get(listing=l);assert r.reason=='manual_change_only' and r.intent_id is None
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now+timedelta(seconds=6))
r.refresh_from_db();assert r.intent_id is None
""",
                "manual_defect": """
from garimpei.main import build_classify_condition,build_read_condition
e['description']='Não foi testado.';l.latest.evidence=e;l.latest.save()
condition=build_read_condition().execute(l.id)
build_classify_condition().execute(l.id,'defect',condition.state.revision)
e['description']='Funciona perfeitamente. Controle original incluído.';l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l);assert r.reason=='condition_excluded' and r.intent_id is None
from garimpei.main import build_read_alert_diagnostic
assert build_read_condition().execute(l.id).state.effective=='defect'
d=build_read_alert_diagnostic().execute(l.id,l.latest_id)
assert d.current_reason=='condition_excluded' and d.first_alert_state=='not_sent'
""",
                "stale_observation": """
from garimpei.infra.persistence.listing_models import CollectionCycle,ListingObservation,ListingInterestMatch
signature=s.prepare(l.id);profit=build_read_profit().execute(l.id);old=l.latest
cycle=CollectionCycle.objects.create(state=old.cycle.state,scope_key=old.cycle.scope_key,revision=old.cycle.revision,phase='complete',started_at=now,finished_at=now)
new=ListingObservation.objects.create(listing=l,cycle=cycle,ordinal=old.ordinal+1,observed_at=now,price=old.price,evidence=old.evidence,coverage=old.coverage,provenance=old.provenance)
for match in old.matches.all():ListingInterestMatch.objects.create(observation=new,kind=match.kind,key=match.key)
l.latest=new;l.save()
s.publish(l.id,signature,profit,now)
r=FirstAlertIdentity.objects.get(listing=l);assert r.reason=='profit_observation_mismatch' and r.intent_id is None
stale=r.decisions.latest('generation').id
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now+timedelta(seconds=1))
r.refresh_from_db();assert r.intent_id is not None
assert r.decisions.get(id=stale).reason=='profit_observation_mismatch'
""",
                "history_unavailable": """
from garimpei.infra.persistence.alert_models import AlertFeedCursor
from garimpei.main import build_read_alert_diagnostic
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l);AlertFeedCursor.objects.update(history_ready=False)
assert store.claim(r.intent_id,binding,now,reconcile=False) is None
d=build_read_alert_diagnostic().execute(l.id,l.latest_id)
assert d.reason=='history_unavailable' and d.state=='suspended'
""",
                "oscillation": """
from garimpei.domain.alert.alert import Outcome,Receipt
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l);first=r.intent_id
delivery=store.claim(first,binding,now,reconcile=False)
store.finish(delivery,Outcome('confirmed','ack',Receipt('original-receipt',True,binding.recipient,delivery.body,1)),now)
for index,text in enumerate(('Não foi testado.','Funciona perfeitamente.','Com defeito.','Funciona perfeitamente.')):
 e['description']=text;l.latest.evidence=e;l.latest.save();s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now+timedelta(seconds=index+1))
 r.refresh_from_db();assert r.intent_id==first
from dataclasses import replace
profit=build_read_profit().execute(l.id)
changed=replace(profit,policy=profit.policy+'-revision-2')
s.publish(l.id,s.prepare(l.id),changed,now+timedelta(seconds=10))
r.refresh_from_db();assert r.intent_id==first
assert r.decisions.latest('generation').financial['policy']==changed.policy
assert AlertIntent.objects.filter(first_decision__identity=r).count()==1
assert store.claim(first,Binding('new','300@g.us','400@c.us'),now+timedelta(seconds=20),reconcile=False) is None
""",
            }
            script = scripts[case]
            if case in {"zero", "negative"}:
                row = first_cases()["variations"][case]
                price = row["price"].replace(",", ".")
                script = script.replace("1350.00" if case == "zero" else "1400.00", price)
            shell(instance, PREPARE + script)
            if case == "inventory_barrier":
                assert not any(method == "POST" for method, _ in channel.calls)
        finally:
            resume_worker(group)
        if case == "manual_race":
            from tests.integration.test_collection import command

            command(instance, "./scripts/stop.sh")
            command(instance, "./scripts/init.sh", "--disposable")
            shell(
                instance,
                """
from garimpei.main import build_alert_handler,build_read_condition
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
for stage in ('adopt','refresh','send'):build_alert_handler(stage).execute()
l=Listing.objects.get(external_id='16001');r=FirstAlertIdentity.objects.get(listing=l)
assert r.intent_id is None and r.reason=='manual_change_only'
assert build_read_condition().execute(l.id).state.manual=='good'
""",
            )
            assert not any(method == "POST" for method, _ in channel.calls)


def test_slow_channel_check_crossing_publication_deadline_never_posts(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, clock, channel):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                PREPARE
                + """
e['published_at']=(now-timedelta(hours=48)+timedelta(seconds=1)).isoformat();l.latest.evidence=e;l.latest.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
assert FirstAlertIdentity.objects.get(listing=l).intent_id is not None
""",
            )
            channel.hold_check = True
            with ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(
                    instance.shell,
                    "from garimpei.main import build_alert_handler;build_alert_handler('send').execute()",
                )
                assert channel.held.wait(10)
                clock.advance(2)
                channel.release.set()
                process = result.result(timeout=20)
                assert process.returncode == 0, process.stdout + process.stderr
            assert not any(method == "POST" for method, _ in channel.calls)
            shell(
                instance,
                """
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
r=FirstAlertIdentity.objects.get(listing__external_id='16001')
assert r.intent.reason=='publication_expired'
""",
            )
        finally:
            channel.release.set()
            resume_worker(group)
