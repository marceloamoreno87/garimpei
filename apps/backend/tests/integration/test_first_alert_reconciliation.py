from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


@pytest.mark.parametrize(
    "case",
    [
        "original_binding",
        "late_response",
        "late_reconciliation",
        "after_deadline",
        "after_deadline_empty",
    ],
)
def test_reconciliation_keeps_original_effect_and_evidence(tmp_path: Path, case: str) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, channel):
        group = pause_worker(instance)
        try:
            script = """
from garimpei.domain.alert.alert import Outcome,Receipt
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l)
first=store.claim(r.intent_id,binding,now,reconcile=False)
assert first is not None
"""
            if case == "original_binding":
                script += """
store.finish(first,Outcome('uncertain','response_lost'),now)
recovered=store.claim(r.intent_id,Binding('changed','300@g.us','400@c.us'),now+timedelta(seconds=61),reconcile=True)
assert recovered is not None,'original binding reconciliation was blocked by new configuration'
assert recovered.binding==binding and recovered.body==first.body and recovered.reference==first.reference
"""
            elif case == "late_response":
                script += """
newer=store.claim(r.intent_id,binding,now+timedelta(seconds=61),reconcile=True)
assert newer is not None and newer.generation>first.generation
store.finish(first,Outcome('confirmed','late',Receipt('late-known',True,binding.recipient,first.body,2)),now+timedelta(seconds=62))
r.intent.refresh_from_db()
assert r.intent.state != 'confirmed' and r.intent.generation==newer.generation
assert r.intent.attempts.get(generation=first.generation).message_id=='late-known','late receipt evidence was discarded'
"""
            elif case == "late_reconciliation":
                script += """
second=store.claim(r.intent_id,binding,now+timedelta(seconds=61),reconcile=True)
third=store.claim(r.intent_id,binding,now+timedelta(seconds=122),reconcile=True)
assert second is not None and third is not None
store.finish(second,Outcome('confirmed','late-reconciliation',Receipt('reconcile-late-known',True,binding.recipient,second.body,2)),now+timedelta(seconds=123))
r.intent.refresh_from_db()
assert r.intent.state != 'confirmed' and r.intent.generation==third.generation
assert r.intent.attempts.get(generation=first.generation).message_id=='reconcile-late-known','late reconciliation evidence was discarded'
"""
            else:
                channel.mode = "lost"
                script += """
from garimpei.main import _effective_alert_settings,_alert_policy
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
store.finish(first,gateway.send(first),now)
later=now+timedelta(hours=49)
recovered=store.claim(r.intent_id,binding,later,reconcile=True)
assert recovered is not None and recovered.reference==first.reference
store.finish(recovered,gateway.reconcile(recovered,later),later)
r.intent.refresh_from_db();assert r.intent.state=='confirmed' and r.intent.confirmed_at==later
assert r.intent.attempts.count()==1
assert not store.ready(later+timedelta(seconds=100),reconcile=False)
"""
            script += """
from dataclasses import replace
changed=replace(build_read_profit().execute(l.id),policy='changed-policy-v2')
s.publish(l.id,s.prepare(l.id),changed,now+timedelta(hours=50))
assert store.claim(r.intent_id,Binding('changed','300@g.us','400@c.us'),now+timedelta(hours=50),reconcile=False) is None
assert r.intent.attempts.count()==1
"""
            if case == "after_deadline_empty":
                channel.mode = "lost_empty"
                script = script.replace(
                    "assert r.intent.state=='confirmed' and r.intent.confirmed_at==later",
                    "assert r.intent.state=='review' and r.intent.reason=='reconciliation_window_ended' and r.intent.confirmed_at is None",
                )
            shell(instance, PREPARE + script)
            if case in {"after_deadline", "after_deadline_empty"}:
                assert len([call for call in channel.calls if call[0] == "POST"]) == 1
        finally:
            resume_worker(group)


def test_uncertain_reduction_without_current_binding_never_becomes_sendable(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, channel):
        group = pause_worker(instance)
        channel.mode = "lost"
        try:
            shell(
                instance,
                PREPARE
                + """
from garimpei.domain.alert.alert import Outcome,Receipt
from garimpei.infra.persistence.listing_models import CollectionCycle,ListingObservation,ListingInterestMatch
from garimpei.main import _effective_alert_settings,_alert_policy,build_read_listing_changes
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.usecase.alert.reconcile_alert_usecase import ReconcileAlertUseCase
from garimpei.usecase.alert.send_alert_usecase import SendAlertUseCase
from decimal import Decimal
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l);first=store.claim(r.intent_id,binding,now,reconcile=False)
store.finish(first,Outcome('confirmed','baseline',Receipt('first-known',True,binding.recipient,first.body,1)),now)
old=l.latest
cycle=CollectionCycle.objects.create(state=old.cycle.state,scope_key=old.cycle.scope_key,revision=old.cycle.revision,phase='complete',started_at=now,finished_at=now)
e=dict(old.evidence);e['price']='900.00';e['published_at']=(now-timedelta(hours=49)).isoformat()
assert now-__import__('datetime').datetime.fromisoformat(e['published_at']) > timedelta(hours=48)
new=ListingObservation.objects.create(listing=l,cycle=cycle,ordinal=old.ordinal+1,observed_at=now,price=Decimal('900.00'),evidence=e,coverage=old.coverage,provenance=old.provenance)
for match in old.matches.all():ListingInterestMatch.objects.create(observation=new,kind=match.kind,key=match.key)
l.latest=new;l.save()
event=ListingEvent.objects.create(listing=l,observation=new,previous=old,kind='price_decreased',silent=False,occurred_at=now,publication_order=l.publication_order+1)
decision=AlertEventDecision.objects.create(event=event,state='waiting',reason='profit_pending',next_action=now)
store.evaluate(event.id,build_read_profit().execute(event.id,event=True),now)
row=AlertIntent.objects.get(decision=decision)
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
delivery=store.claim(row.id,binding,now,reconcile=False);assert delivery is not None
store.finish(delivery,gateway.send(delivery),now)
ReconcileAlertUseCase(store,gateway,None,lambda:now+timedelta(seconds=61)).execute()
SendAlertUseCase(store,gateway,binding,build_read_listing_changes(),lambda:now+timedelta(seconds=100)).execute()
""",
            )
            assert len([call for call in channel.calls if call[0] == "POST"]) == 1
        finally:
            resume_worker(group)
