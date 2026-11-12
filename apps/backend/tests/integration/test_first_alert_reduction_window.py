from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_cases, first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_reduction_uses_prior_intent_window_and_never_reopens_after_late_confirmation(
    tmp_path: Path, offset: int
) -> None:
    with first_eligibility_scenario(tmp_path, enabled=False) as (instance, _, _, channel):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                PREPARE
                + """
from decimal import Decimal
from garimpei.domain.alert.alert import Outcome,Receipt
from garimpei.main import _alert_policy,_effective_alert_settings
from garimpei.infra.persistence.listing_models import CollectionCycle,ListingObservation,ListingInterestMatch
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from pathlib import Path
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
r=FirstAlertIdentity.objects.get(listing=l)
first=store.claim(r.intent_id,binding,now,reconcile=False)
assert first is not None
frozen_body=first.body;frozen_financial=dict(r.intent.financial)
# The distinct decrease happens one hour after first authorization; its own
# observation/reference is still valid when the prior-intent wait window ends.
event_time=now+timedelta(hours=1)
Path(load_listing_settings().fixture_clock).write_text(event_time.isoformat())
old=l.latest
cycle=CollectionCycle.objects.create(state=old.cycle.state,scope_key=old.cycle.scope_key,revision=old.cycle.revision,phase='complete',started_at=event_time,finished_at=event_time)
e=dict(old.evidence);e['price']='900.00'
observation=ListingObservation.objects.create(listing=l,cycle=cycle,ordinal=old.ordinal+1,observed_at=event_time,price=Decimal('900.00'),evidence=e,coverage=old.coverage,provenance=old.provenance)
for match in old.matches.all():ListingInterestMatch.objects.create(observation=observation,kind=match.kind,key=match.key)
l.latest=observation;l.save()
event=ListingEvent.objects.create(listing=l,observation=observation,previous=old,kind='price_decreased',silent=False,occurred_at=event_time,publication_order=l.publication_order+1)
decision=AlertEventDecision.objects.create(event=event,state='waiting',reason='profit_pending',next_action=event_time)
profit=build_read_profit().execute(event.id,event=True)
assert profit.event_id==event.id and profit.observation_id==observation.id and profit.profit.value==Decimal('450.00')
window=_alert_policy().window
boundary=now+timedelta(seconds=window+"""
                + str(offset)
                + """)
assert boundary-event_time < timedelta(hours=48)
store.evaluate(event.id,profit,boundary)
decision.refresh_from_db()
if """
                + str(offset)
                + """ < 0:
 assert decision.reason=='waiting_previous'
else:
 assert decision.state=='excluded' and decision.reason=='no_previous_confirmation',(decision.state,decision.reason)
# A valid late ACK confirms the original effect. It does not reopen a decrease
# whose waiting policy has already excluded it.
store.finish(first,Outcome('confirmed','prior_ack',Receipt('prior-known',True,binding.recipient,first.body,1)),boundary)
store.evaluate(event.id,profit,boundary+timedelta(seconds=1))
decision.refresh_from_db();r.intent.refresh_from_db()
assert r.intent.state=='confirmed' and r.intent.body==frozen_body and r.intent.financial==frozen_financial
if """
                + str(offset)
                + """ < 0:
 assert decision.state=='eligible'
 reduced=AlertIntent.objects.get(decision=decision)
 delivery=store.claim(reduced.id,binding,boundary+timedelta(seconds=1),reconcile=False)
 assert delivery is not None
 settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
 store.finish(delivery,gateway.send(delivery),boundary+timedelta(seconds=1))
 reduced.refresh_from_db();assert reduced.state=='confirmed'
 assert reduced.financial['event_id']==str(event.id) and reduced.financial['observation_id']==str(observation.id)
 assert 'Preço anterior: R$ 1.000,00' in reduced.body and 'Preço de compra: R$ 900,00' in reduced.body
else:
 assert decision.state=='excluded' and decision.reason=='no_previous_confirmation'
 assert not AlertIntent.objects.filter(decision=decision).exists()
""".replace("900.00", first_cases()["QUEDAS"]["prices"][1]),
            )
            assert sum(method == "POST" for method, _ in channel.calls) == (1 if offset < 0 else 0)
        finally:
            resume_worker(group)
