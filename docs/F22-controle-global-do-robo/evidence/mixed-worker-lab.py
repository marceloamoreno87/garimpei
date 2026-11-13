# Controlled F22 reproduction lab. The recorded run selected the held intent dynamically through SQL assertions; the action below now does the same.
import sys,json,time,hashlib
from pathlib import Path
from datetime import timedelta
from threading import Event
from tests.factories.first_eligibility import first_eligibility_scenario,TITLE
from tests.factories.valuation import listing
from tests.factories.runtime import pause_worker,resume_worker
from tests.integration.test_collection import shell,sql,command,wait_for

class MessageBarrier(Event):
 def wait(self,timeout=None):return super().wait(120)
private=Path(sys.argv[1]);private.mkdir(parents=True,exist_ok=True)
group=0
with first_eligibility_scenario(private,sample_ready=False) as (instance,source,clock,channel):
 with instance.private_file.open('a') as env:env.write('GARIMPEI_ALERT_TIMEOUT=40\n')
 command(instance,'./scripts/stop.sh');command(instance,'./scripts/init.sh','--disposable')
 source.rows['16008']=listing('16008','1100,00',title=TITLE,description='Com defeito. Não funciona.',published_at=(clock.value-timedelta(hours=2)).isoformat(),shipping_offered=True)
 def state(action):
  rows=sql(instance,"SELECT coalesce(l.external_id,'legacy'),i.id::text,i.state,i.reason,i.body,i.confirmed_message,(SELECT count(*) FROM runtime_alertattempt a WHERE a.intent_id=i.id) FROM runtime_alertintent i LEFT JOIN runtime_firsteligibilitydecision d ON d.id=i.first_decision_id LEFT JOIN runtime_firstalertidentity f ON f.id=d.identity_id LEFT JOIN runtime_listing l ON l.id=f.listing_id ORDER BY i.created_at")
  print(json.dumps({'action':action,'url':f'http://127.0.0.1:{instance.config.web_port}','posts':len([c for c in channel.calls if c[0]=='POST']),'messages':len(channel.messages),'control':sql(instance,'SELECT requested_enabled,revision FROM runtime_robotcontrol'),'intents':[{'listing':r[0],'id':r[1],'state':r[2],'reason':r[3],'body_sha256':hashlib.sha256(r[4].encode()).hexdigest(),'receipt':r[5],'attempts':r[6]} for r in rows],'source_and_valuation_requests':len(source.calls)},default=str),flush=True)
 state('ready')
 try:
  for raw in sys.stdin:
   action=raw.strip()
   if action=='arm':
    channel.mode='lost_empty';channel.hold_post=True;channel.release=MessageBarrier();channel.held.clear()
    source.rows['16006']['description']='Funciona perfeitamente.';source.rows['16001']['description']='Usado. Funciona perfeitamente.';source.rows['16001']['price']='R$ 1.050,00'
    clock.advance(61)
    wait_for(channel.held.is_set,'initial authorized POST held',seconds=55)
    wait_for(lambda:sql(instance,"SELECT count(*) FROM runtime_valuationprogress p JOIN runtime_listing l ON l.id=p.listing_id WHERE l.external_id='16008' AND p.current_id IS NOT NULL")==[(1,)],'expired candidate valuation',seconds=12)
    held_id=sql(instance,"SELECT id::text FROM runtime_alertintent WHERE state='authorized' ORDER BY created_at LIMIT 1")[0][0]
    (private/'held-intent.json').write_text(json.dumps(held_id))
    group=pause_worker(instance)
    clock.advance(61)
    shell(instance,"""
from uuid import uuid4
from garimpei.main import build_first_alert_store,build_read_profit,build_valuation_store,reconcile_listings,_enqueue,_defer_valuation,_listing_clock
from garimpei.config.env import load_listing_settings
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.valuation_models import ValuationWork,ValuationProgress
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
from garimpei.infra.persistence.media_models import MediaCapture,MediaEntry,MediaJob
from garimpei.infra.persistence.inference_models import InferenceControl
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.domain.inference.request import AnalysisInput
from garimpei.domain.inference.ports import PreparedPart
now=_listing_clock(load_listing_settings())()
expired=Listing.objects.select_related('latest').get(external_id='16008')
e=dict(expired.latest.evidence);e['description']='Usado. Funciona perfeitamente.';expired.latest.evidence=e;expired.latest.save()
first=build_first_alert_store();first.publish(expired.id,first.prepare(expired.id),build_read_profit().execute(expired.id),now)
assert FirstAlertIdentity.objects.get(listing=expired).intent.state=='queued'
reconcile_listings()
target=Listing.objects.select_related('latest').get(external_id='16001')
progress=ValuationProgress.objects.select_related('current__work').get(listing=target)
progress.requested+=1;progress.save(update_fields=['requested'])
work=ValuationWork.objects.create(listing=target,revision=progress.requested,snapshot=progress.current.work.snapshot,requested_at=now,next_attempt_at=now,lease_until=now+__import__('datetime').timedelta(seconds=60),attempts=1)
_defer_valuation(work.id)
capture,_=MediaCapture.objects.get_or_create(observation=target.latest,defaults=dict(observed_at=now))
entry=MediaEntry.objects.create(capture=capture,photo_key='paused-photo',position=0,candidates=[dict(url='http://127.0.0.1:1/not-contacted',width=None,height=None)])
media=MediaJob.objects.create(entry=entry,kind='download',next_at=now)
_enqueue('garimpei.media','media',0,job_id=str(media.id))
repo=PostgresInferenceRepository(lambda:_enqueue('garimpei.local_analysis','inference',0),5)
repo.admit(AnalysisInput(target.latest_id,target.latest.ordinal,'Controlled queued input',()),'controlled-artifact',(PreparedPart('text','Controlled queued input'),))
""")
    job_rows=sql(instance,"SELECT id,task_name,status FROM procrastinate_jobs WHERE status='todo' AND task_name IN ('garimpei.collect_listings','garimpei.evaluate_valuation','garimpei.media','garimpei.local_analysis') ORDER BY id")
    assert len({r[1] for r in job_rows})==4,job_rows
    (private/'queued.json').write_text(json.dumps([list(r) for r in job_rows],default=str))
    print(json.dumps({'queued_before_pause':[list(r) for r in job_rows],'worker_group_frozen':True},default=str),flush=True)
    state(action)
   elif action=='drain':
    resume_worker(group);group=0
    channel.release.set();channel.hold_post=False
    ids=[r[0] for r in json.loads((private/'queued.json').read_text())]
    wait_for(lambda:sql(instance,"SELECT count(*) FROM procrastinate_jobs WHERE id=ANY(ARRAY["+','.join(str(i) for i in ids)+"]) AND status IN ('todo','doing')")==[(0,)],'old queued jobs consumed under pause',seconds=20)
    assert not sql(instance,"SELECT id FROM procrastinate_jobs WHERE id=ANY(ARRAY["+','.join(str(i) for i in ids)+"]) AND status='failed'")
    wait_for(lambda:sql(instance,"SELECT count(*) FROM runtime_alertintent WHERE state='uncertain'")==[(1,)],'lost POST becomes uncertain',seconds=20)
    shell(instance,"""
from garimpei.infra.persistence.media_models import MediaJob
from garimpei.infra.persistence.inference_models import InferencePart
from garimpei.infra.persistence.valuation_models import ValuationWork
assert MediaJob.objects.get(entry__photo_key='paused-photo').attempts==0
assert InferencePart.objects.get().attempts==0 and InferencePart.objects.get().state=='pending'
assert ValuationWork.objects.filter(completed=False,attempts=0,lease_until=None).exists()
""")
    state(action)
   elif action=='restart-uncertain':
    clock.advance(61)
    command(instance,'./scripts/stop.sh');command(instance,'./scripts/init.sh','--disposable')
    assert sql(instance,'SELECT requested_enabled FROM runtime_robotcontrol')==[(False,)]
    assert len([c for c in channel.calls if c[0]=='POST'])==1
    state(action)
   elif action=='prepare-mixed-resume':
    clock.advance(49*3600)
    source.rows['16008']['description']='Usado. Funciona perfeitamente.'
    source.rows['16007']=listing('16007','800,00',title=TITLE,description='Usado. Funciona perfeitamente.',published_at=clock.value.isoformat(),shipping_offered=True)
    channel.mode='confirmed'
    shell(instance,"""
from garimpei.infra.persistence.inference_models import InferenceControl
InferenceControl.objects.get_or_create(pk=1);InferenceControl.objects.filter(pk=1).update(paused=True)
""")
    state(action)
   elif action=='wait-mixed-resume':
    next_clock=time.monotonic()+6
    def valid_sent():
     return any('/item/16007/' in str(m['body']) for m in channel.messages)
    deadline=time.monotonic()+60
    while time.monotonic()<deadline and not valid_sent():
     if time.monotonic()>=next_clock:clock.advance(6);next_clock=time.monotonic()+6
     time.sleep(.1)
    assert valid_sent(),'new valid listing did not confirm'
    assert len([c for c in channel.calls if c[0]=='POST'])==2
    assert not any('/item/16008/' in str(m['body']) or '/item/16001/' in str(m['body']) for m in channel.messages)
    shell(instance,"""
from garimpei.infra.persistence.alert_models import FirstAlertIdentity,AlertIntent
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.inference_models import InferenceControl
old=AlertIntent.objects.get(pk=HELD_INTENT_ID)
expired=FirstAlertIdentity.objects.get(listing__external_id='16008')
valid=FirstAlertIdentity.objects.get(listing__external_id='16007').intent
assert old.state in ('uncertain','review') and old.attempts.count()==1 and old.confirmed_message is None
assert expired.reason=='publication_expired' and expired.intent.attempts.count()==0
assert valid.state=='confirmed' and valid.attempts.count()==1
assert InferenceControl.objects.get(pk=1).paused
""".replace('HELD_INTENT_ID',repr(json.loads((private/'held-intent.json').read_text()))))
    state(action)
   elif action=='inspect':state(action)
   elif action=='exit':break
   else:raise RuntimeError('unknown action')
 finally:
  if group:resume_worker(group)
