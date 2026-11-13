from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell

PREPARE = """
from datetime import timedelta
from garimpei.main import build_first_alert_store,build_read_profit,build_alert_store,_listing_clock
from garimpei.config.env import load_listing_settings
from garimpei.domain.alert.alert import Binding
from garimpei.infra.persistence.listing_models import Listing,ListingEvent
from garimpei.infra.persistence.alert_models import AlertIntent,AlertEventDecision,FirstAlertIdentity,FirstAlertInventory
from garimpei.infra.repository.alert.financial import financial_snapshot
from garimpei.infra.persistence.valuation_models import ValuationProgress
now=_listing_clock(load_listing_settings())()
l=Listing.objects.select_related('latest').get(external_id='16001')
e=dict(l.latest.evidence);e['description']='Funciona perfeitamente.';l.latest.evidence=e;l.latest.save()
s=build_first_alert_store();store=build_alert_store();binding=Binding('synthetic','100@g.us','200@c.us')
s.adopt(now)
# History readiness is an explicit precondition, independent of scheduler timing.
from garimpei.main import build_alert_handler
build_alert_handler('ingest').execute()
"""


def test_prepare_adopts_before_publication_even_when_worker_has_not_adopted(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, _):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                """
from garimpei.infra.persistence.alert_models import AlertIntent,FirstAlertIdentity,FirstEligibilityDecision
from garimpei.infra.persistence.listing_models import Listing
target=Listing.objects.get(external_id='16001')
# Reproduce the scheduler boundary explicitly, before any effect was authorized.
assert not AlertIntent.objects.filter(first_decision__identity__listing=target).exists()
FirstEligibilityDecision.objects.filter(identity__listing=target).delete()
FirstAlertIdentity.objects.filter(listing=target).delete()
assert not FirstAlertIdentity.objects.filter(listing=target).exists()
"""
                + PREPARE
                + """
assert FirstAlertIdentity.objects.filter(listing=l).exists()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
first=FirstAlertIdentity.objects.get(listing=l)
assert first.intent_id is not None
identity=first.intent_id
s.adopt(now)
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
first.refresh_from_db()
assert first.intent_id==identity
assert AlertIntent.objects.filter(first_decision__identity__listing=l).count()==1
""",
            )
        finally:
            resume_worker(group)


@pytest.mark.parametrize(
    "case", ["legacy_queued_expired", "legacy_waiting", "financial_expired", "safe_retry_refresh"]
)
def test_final_authorization_and_adoption_guards(tmp_path: Path, case: str) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, _):
        group = pause_worker(instance)
        try:
            if case == "legacy_queued_expired":
                script = """
e['published_at']=(now-timedelta(hours=49)).isoformat();l.latest.evidence=e;l.latest.save()
event=ListingEvent.objects.create(listing=l,observation=l.latest,kind='discovered',silent=False,occurred_at=now,publication_order=l.publication_order)
state,reason,financial=financial_snapshot(event,build_read_profit().execute(event.id,event=True))
decision=AlertEventDecision.objects.create(event=event,state='eligible',reason=reason,financial=financial,next_action=now)
legacy=AlertIntent.objects.create(decision=decision,created_at=now,next_action=now)
FirstAlertInventory.objects.update(completed=False,cursor=None)
s.adopt(now)
assert store.claim(legacy.id,binding,now,reconcile=False) is None,'expired legacy queued intent bypassed first-alert policy'
"""
            elif case == "legacy_waiting":
                script = """
event=ListingEvent.objects.create(listing=l,observation=l.latest,kind='discovered',silent=False,occurred_at=now,publication_order=l.publication_order)
decision=AlertEventDecision.objects.create(event=event,state='waiting',reason='profit_pending',next_action=now)
FirstAlertInventory.objects.update(completed=False,cursor=None)
s.adopt(now)
store.evaluate(event.id,build_read_profit().execute(event.id,event=True),now)
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
assert AlertIntent.objects.filter(decision=decision).count()==0,'legacy waiting created a second discovery path'
assert FirstAlertIdentity.objects.get(listing=l).intent_id is not None
"""
            elif case == "financial_expired":
                script = """
p=ValuationProgress.objects.select_related('current').get(listing=l)
r=dict(p.current.result);r['resale']=dict(r['resale']);r['resale']['valid_until']=(now+timedelta(seconds=1)).isoformat();p.current.result=r;p.current.save()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
first=FirstAlertIdentity.objects.get(listing=l)
assert first.intent_id is not None,first.reason
assert store.claim(first.intent_id,binding,now+timedelta(seconds=2),reconcile=False) is None,'expired financial evidence authorized after channel wait'
"""
            else:
                script = """
from garimpei.domain.alert.alert import Outcome
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l)
old=r.intent;delivery=store.claim(old.id,binding,now,reconcile=False)
assert delivery is not None
store.finish(delivery,Outcome('safe_retry','not_transmitted'),now)
body=AlertIntent.objects.get(id=old.id).body
MonitoringConfiguration.objects.filter(slot='active').update(revision=10,resale_fee_percent='11.00')
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now+timedelta(seconds=20))
r.refresh_from_db();old.refresh_from_db()
assert old.body==body,'authorized body rewritten'
assert r.intent_id != old.id and old.state=='cancelled','proven unsent stale intent was not replaced'
assert store.claim(r.intent_id,binding,now+timedelta(seconds=20),reconcile=False) is not None
"""
            shell(instance, PREPARE + script)
        finally:
            resume_worker(group)
