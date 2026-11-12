from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


@pytest.mark.parametrize(
    "case",
    [
        "legacy_queued_partial",
        "legacy_conflict",
        "legacy_authorized",
        "legacy_review",
        "isolated_profit_failure",
    ],
)
def test_inventory_and_independent_recovery(tmp_path: Path, case: str) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _, _, channel):
        group = pause_worker(instance)
        try:
            common = (
                PREPARE
                + """
from garimpei.main import _effective_alert_settings,_alert_policy,build_read_alert_diagnostic,build_read_listing_changes
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.usecase.alert.send_alert_usecase import SendAlertUseCase
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
"""
            )
            if case == "legacy_queued_partial":
                script = """
from garimpei.infra.persistence.listing_models import CollectionState,CollectionCycle
CollectionState.objects.update(initial_completed_at=None)
CollectionCycle.objects.filter(id=l.latest.cycle_id).update(phase='partial')
event=ListingEvent.objects.create(listing=l,observation=l.latest,kind='discovered',silent=False,occurred_at=now,publication_order=l.publication_order)
_,_,financial=financial_snapshot(event,build_read_profit().execute(event.id,event=True))
decision=AlertEventDecision.objects.create(event=event,state='eligible',reason='eligible',financial=financial,next_action=now)
legacy=AlertIntent.objects.create(decision=decision,created_at=now,next_action=now)
reference=legacy.id
FirstAlertInventory.objects.update(completed=False,cursor=None)
s.adopt(now)
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l)
assert r.intent_id==reference and r.intent.first_decision_id is not None
SendAlertUseCase(store,gateway,binding,build_read_listing_changes(),lambda:now).execute()
legacy.refresh_from_db();assert legacy.state=='confirmed'
assert legacy.decision.financial==financial
assert CollectionCycle.objects.get(id=l.latest.cycle_id).phase=='partial'
assert CollectionState.objects.filter(initial_completed_at__isnull=True).exists()
s.adopt(now);s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
SendAlertUseCase(store,gateway,binding,build_read_listing_changes(),lambda:now+timedelta(seconds=6)).execute()
assert FirstAlertIdentity.objects.get(listing=l).intent_id==reference
"""
            elif case == "legacy_conflict":
                script = """
from garimpei.infra.persistence.alert_models import AlertAttempt
known=[]
for index,kind in enumerate(('discovered','price_decreased')):
 event=ListingEvent.objects.create(listing=l,observation=l.latest,kind=kind,silent=False,occurred_at=now,publication_order=l.publication_order)
 decision=AlertEventDecision.objects.create(event=event,state='eligible',reason='eligible',next_action=now)
 intent=AlertIntent.objects.create(decision=decision,body=f'IMMUTABLE LEGACY {index}',session=binding.session,recipient=binding.recipient,account=binding.account,state='uncertain',reason='response_lost',created_at=now,next_action=now)
 attempt=AlertAttempt.objects.create(intent=intent,ordinal=1,generation=1,authorized_at=now)
 known.append((intent.id,intent.body,attempt.id))
FirstAlertInventory.objects.update(completed=False,cursor=None)
s.adopt(now);s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
SendAlertUseCase(store,gateway,binding,build_read_listing_changes(),lambda:now).execute()
assert AlertIntent.objects.filter(decision__event__listing=l).count()==2
for identity,body,attempt in known:
 intent=AlertIntent.objects.get(id=identity);assert intent.body==body and intent.attempts.get().id==attempt
assert not AlertIntent.objects.filter(first_decision__identity__listing=l).exists()
d=build_read_alert_diagnostic().execute(l.id,l.latest_id)
assert d.state=='history_review','multiple possible legacy transmissions must explicitly require review'
"""
            elif case in {"legacy_authorized", "legacy_review"}:
                script = """
from garimpei.infra.persistence.alert_models import AlertAttempt
event=ListingEvent.objects.create(listing=l,observation=l.latest,kind='discovered',silent=False,occurred_at=now,publication_order=l.publication_order)
decision=AlertEventDecision.objects.create(event=event,state='eligible',reason='eligible',next_action=now)
legacy=AlertIntent.objects.create(decision=decision,state=STATE,reason='legacy_possible',body='IMMUTABLE LEGACY',session=binding.session,recipient=binding.recipient,account=binding.account,created_at=now,next_action=now)
attempt=AlertAttempt.objects.create(intent=legacy,ordinal=1,generation=1,authorized_at=now)
FirstAlertInventory.objects.update(completed=False,cursor=None)
s.adopt(now);s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
SendAlertUseCase(store,gateway,binding,build_read_listing_changes(),lambda:now).execute()
legacy.refresh_from_db();r=FirstAlertIdentity.objects.get(listing=l)
assert r.intent_id==legacy.id and legacy.body=='IMMUTABLE LEGACY'
assert legacy.attempts.get().id==attempt.id and legacy.recipient==binding.recipient
assert not AlertIntent.objects.filter(first_decision__identity=r).exclude(id=legacy.id).exists()
d=build_read_alert_diagnostic().execute(l.id,l.latest_id);assert d.state in {'authorized','review','uncertain'}
""".replace("STATE", repr(case.removeprefix("legacy_")))
            else:
                script = """
from copy import deepcopy
from uuid import uuid4
from garimpei.infra.persistence.listing_models import ListingObservation,ListingInterestMatch
from garimpei.infra.persistence.valuation_models import ValuationWork,ValuationEvaluation
from garimpei.domain.valuation.profit_queries import ProfitReadFailed
from garimpei.usecase.alert.refresh_first_eligibility_usecase import RefreshFirstEligibilityUseCase
new=Listing.objects.create(source=l.source,external_id='16007',canonical_url='https://www.facebook.com/marketplace/item/16007/',first_seen_at=now,origin='initial',ordinal=1)
obs=ListingObservation.objects.create(listing=new,cycle=l.latest.cycle,ordinal=1,observed_at=now,price=l.latest.price,evidence=l.latest.evidence,coverage=l.latest.coverage,provenance=l.latest.provenance)
for match in l.latest.matches.all():ListingInterestMatch.objects.create(observation=obs,kind=match.kind,key=match.key)
new.latest=obs;new.save()
previous=ValuationProgress.objects.select_related('current__work').get(listing=l)
snapshot=deepcopy(previous.current.work.snapshot);snapshot['target']['listing_id']=str(new.id);snapshot['target']['external_id']='16007';snapshot['target']['url']=new.canonical_url
work=ValuationWork.objects.create(listing=new,revision=1,snapshot=snapshot,requested_at=now,next_attempt_at=now,completed=True)
value=deepcopy(previous.current.result);value['id']=str(uuid4());value['listing_id']=str(new.id);value['revision']=1;value['input_revision']=1
evaluation=ValuationEvaluation.objects.create(id=value['id'],work=work,result=value)
ValuationProgress.objects.create(listing=new,requested=1,signature='synthetic equivalent input',current=evaluation)
s.adopt(now);FirstAlertIdentity.objects.filter(listing_id__in=(l.id,new.id)).update(next_action=now)
class SelectiveProfitQuery:
 def execute(self,identity,*,event=False):
  if identity==l.id:raise ProfitReadFailed()
  return build_read_profit().execute(identity,event=event)
RefreshFirstEligibilityUseCase(s,SelectiveProfitQuery(),lambda:now).execute()
failed=FirstAlertIdentity.objects.get(listing=l);healthy=FirstAlertIdentity.objects.get(listing=new)
assert failed.reason=='profit_query_failed' and failed.intent_id is None
assert now < failed.next_action <= now+timedelta(seconds=5)
assert healthy.intent_id is not None and healthy.reason=='eligible'
SendAlertUseCase(store,gateway,binding,build_read_listing_changes(),lambda:now).execute()
healthy.intent.refresh_from_db();assert healthy.intent.state=='confirmed'
from garimpei.infra.repository.alert.first_inputs import invalidate_first_alert
invalidate_first_alert(l.id,now+timedelta(seconds=1));failed.refresh_from_db()
assert failed.next_action==now+timedelta(seconds=1)
"""
            shell(instance, common + script)
            if case == "isolated_profit_failure":
                shell(
                    instance,
                    common
                    + """
from garimpei.usecase.alert.refresh_first_eligibility_usecase import RefreshFirstEligibilityUseCase
new=Listing.objects.get(external_id='16007');healthy=FirstAlertIdentity.objects.get(listing=new)
receipt=healthy.intent.confirmed_message;reference=healthy.intent_id
fresh=build_first_alert_store()
RefreshFirstEligibilityUseCase(fresh,build_read_profit(),lambda:now+timedelta(seconds=2)).execute()
failed=FirstAlertIdentity.objects.get(listing=l)
assert failed.intent_id is not None and failed.reason=='eligible'
assert failed.decisions.order_by('-generation').first().cause=='automatic_input'
healthy.refresh_from_db();assert healthy.intent_id==reference and healthy.intent.confirmed_message==receipt
""",
                )
            expected = 0 if case in {"legacy_conflict", "legacy_authorized", "legacy_review"} else 1
            assert len([call for call in channel.calls if call[0] == "POST"]) == expected
        finally:
            resume_worker(group)
