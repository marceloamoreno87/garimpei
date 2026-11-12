from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_eligibility import target_messages


def test_media_only_changes_preserve_consumed_manual_input_and_never_reopen_first_alert(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, _source, _clock, channel):
        group = pause_worker(instance)
        try:
            shell(
                instance,
                """
from copy import deepcopy
from garimpei.main import build_read_condition,build_classify_condition,build_first_alert_store,build_read_profit,_listing_clock
from garimpei.config.env import load_listing_settings
from garimpei.infra.persistence.listing_models import Listing,ListingEvent,ManualCondition
from garimpei.infra.persistence.alert_models import FirstAlertIdentity,AlertIntent,AlertAttempt
from garimpei.infra.persistence.valuation_models import ValuationWork
from garimpei.infra.repository.alert.first_inputs import automatic_signature,semantic_candidates
l=Listing.objects.select_related('latest').get(external_id='16001')
evidence=dict(l.latest.evidence);evidence.pop('media',None);l.latest.evidence=evidence;l.latest.save()
work=ValuationWork.objects.filter(listing=l).order_by('-revision').first()
snapshot=deepcopy(work.snapshot)
for candidate in snapshot.get('candidates',[]):candidate.get('evidence',{}).pop('media',None)
work.snapshot=snapshot;work.save()
condition=build_read_condition().execute(l.id)
build_classify_condition().execute(l.id,'good',condition.state.revision)
store=build_first_alert_store();now=_listing_clock(load_listing_settings())()
store.adopt(now);store.publish(l.id,store.prepare(l.id),build_read_profit().execute(l.id),now)
identity=FirstAlertIdentity.objects.get(listing=l)
assert identity.reason=='manual_change_only' and identity.intent_id is None
baseline=automatic_signature(l);semantic=semantic_candidates(snapshot.get('candidates',[]))
manual=identity.manual_signature
before_events=list(ListingEvent.objects.values_list('id','kind'))
before_intents=list(AlertIntent.objects.values_list('id','confirmed_message','confirmed_ack'))
before_attempts=list(AlertAttempt.objects.values_list('id','state'))
for media in (None, {'presence':'unknown','photos':[]}, {'presence':'present','photos':[{'key':'photo1','primary':True,'correlated':True,'variants':[{'url':'https://a.fbcdn.net/p?signature=renewed','width':1280,'height':960}]}],'complete':True}):
    current=dict(evidence);current['media']=media;current['image_url']='https://a.fbcdn.net/new?signature=changed'
    l.latest.evidence=current;l.latest.save()
    changed=deepcopy(snapshot)
    for candidate in changed.get('candidates',[]):
        candidate.setdefault('evidence',{})['media']=media
        candidate['evidence']['image_url']='https://a.fbcdn.net/another?signature=rotated'
    work.snapshot=changed;work.save()
    assert semantic_candidates(changed.get('candidates',[]))==semantic
    assert automatic_signature(l)==baseline
    store.publish(l.id,store.prepare(l.id),build_read_profit().execute(l.id),now)
    identity.refresh_from_db()
    assert identity.manual_signature==manual and identity.intent_id is None and identity.reason=='manual_change_only'
assert list(ListingEvent.objects.values_list('id','kind'))==before_events
assert list(AlertIntent.objects.values_list('id','confirmed_message','confirmed_ack'))==before_intents
assert list(AlertAttempt.objects.values_list('id','state'))==before_attempts
assert ManualCondition.objects.get(listing=l).choice=='good'
print('media key adoption, new photos and signed-URL rotation keep manual input consumed; no intent/event/receipt changes')
""",
            )
        finally:
            resume_worker(group)
        assert not target_messages(channel)
