from pathlib import Path
import sys,json,hashlib
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'apps/backend'))
from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker,resume_worker
from tests.integration.test_collection import shell,command
private=root/'.runtime/f18-execution/ac14-private';private.mkdir(exist_ok=True)
with first_eligibility_scenario(private,target_title='PlayStation 5 Slim disco',target_description='Usado. Funciona perfeitamente.') as (instance,source,clock,channel):
 worker=pause_worker(instance)
 try:
  shell(instance,"""
from datetime import timedelta
from garimpei.main import build_identity_repository,build_read_profit,build_first_alert_store,build_valuation_store,build_alert_handler,_listing_clock
from garimpei.config.env import load_listing_settings
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.usecase.valuation.evaluate_usecase import EvaluateValuationUseCase
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.valuation_models import ValuationWork
from garimpei.infra.persistence.alert_models import FirstAlertIdentity,AlertIntent
from tests.factories.comparable_research import seed_case
now=_listing_clock(load_listing_settings())()
manual=tuple(sorted(dict(family='playstation5',model='ps5',generation='slim',edition='disc',capacity='1tb').items()))
identity=build_identity_repository()
for external,mode in [('19601','old'),('19602','missing'),('19603','conflict'),('19604','uncertain')]:
 l=seed_case(external,title='PlayStation 5 Slim disco',price='500')
 e=dict(l.latest.evidence);e['published_at']=(now-timedelta(hours=49) if mode=='old' else now-timedelta(hours=1)).isoformat();e['published_at_source']='fixture.published_at'
 if mode=='missing':e['published_at']=None;e['published_at_source']=None
 l.latest.evidence=e;l.latest.save()
 identity.save(IdentityEdit(l.id,l.latest.ordinal,0,'save',manual))
 if mode=='conflict':
  l=seed_case(external,title='PlayStation 5 Slim disco 825GB',price='500')
  e=dict(l.latest.evidence);e['published_at']=(now-timedelta(hours=1)).isoformat();e['published_at_source']='fixture.published_at';l.latest.evidence=e;l.latest.save()
  assert identity.read(l.id).result.state=='conflicting_identity'
store=build_valuation_store();store.reconcile(now)
class NoRetail:
 def offers(self,product,at):return ()
evaluate=EvaluateValuationUseCase(store,NoRetail(),lambda:now)
for work in list(ValuationWork.objects.filter(completed=False).values_list('id',flat=True)):evaluate.execute(work)
first=build_first_alert_store();first.adopt(now)
for external,reason in [('19601','publication_expired'),('19602','publication_missing'),('19603','identidade_conflitante'),('19604','eligible')]:
 l=Listing.objects.get(external_id=external)
 first.publish(l.id,first.prepare(l.id),build_read_profit().execute(l.id),now)
 r=FirstAlertIdentity.objects.get(listing=l)
 if external=='19603': assert r.intent_id is None and r.reason in {'identidade_em_conflito'},r.reason
 else: assert r.reason==reason,(external,r.reason)
 if external!='19604':assert r.intent_id is None,(external,r.reason)
 else:assert r.intent_id is not None,r.reason
""")
  channel.mode='lost_empty'
  shell(instance,"from garimpei.main import build_alert_handler;build_alert_handler('send').execute()")
  with instance.database() as db:
   rows=db.execute("SELECT l.external_id,f.reason,i.state,i.body,i.id,(SELECT count(*) FROM runtime_alertattempt a WHERE a.intent_id=i.id) FROM runtime_firstalertidentity f JOIN runtime_listing l ON l.id=f.listing_id LEFT JOIN runtime_alertintent i ON i.id=f.intent_id WHERE l.external_id IN ('19601','19602','19603','19604') ORDER BY l.external_id").fetchall()
  print('MATRIX_BEFORE',[(r[0],r[1],r[2],r[5]) for r in rows],flush=True)
  uncertain=next(r for r in rows if r[0]=='19604');assert uncertain[2]=='uncertain' and uncertain[5]==1,uncertain[:3]
  bodyhash=hashlib.sha256(uncertain[3].encode()).hexdigest();intent=str(uncertain[4]);posts=channel.calls.count(('POST','/api/sendText'));assert posts==1,posts
 finally:resume_worker(worker)
 command(instance,'./scripts/stop.sh');command(instance,'./scripts/init.sh','--disposable')
 worker=pause_worker(instance)
 try:
  shell(instance,"""
from garimpei.main import build_identity_repository,build_alert_handler
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.infra.persistence.listing_models import Listing
l=Listing.objects.get(external_id='19604');store=build_identity_repository();v=store.read(l.id)
store.save(IdentityEdit(l.id,l.latest.ordinal,v.result.manual_revision,'save',v.manual_values))
for stage in ('adopt','refresh','send'):build_alert_handler(stage).execute()
from tests.factories.comparable_research import seed_case
from garimpei.main import build_read_profit
l=seed_case('19604',title='PlayStation 5 Slim disco 825GB',price='500')
assert store.read(l.id).result.state=='conflicting_identity'
p=build_read_profit().execute(l.id);assert p.resale.value is None and p.profit.value is None
for stage in ('adopt','refresh','send'):build_alert_handler(stage).execute()
""")
  with instance.database() as db:
   after=db.execute("SELECT i.id,i.body,i.state,(SELECT count(*) FROM runtime_alertattempt a WHERE a.intent_id=i.id) FROM runtime_firstalertidentity f JOIN runtime_listing l ON l.id=f.listing_id JOIN runtime_alertintent i ON i.id=f.intent_id WHERE l.external_id='19604'").fetchone()
  assert after and str(after[0])==intent and hashlib.sha256(after[1].encode()).hexdigest()==bodyhash and after[2]=='uncertain' and after[3]==1,after
  assert channel.calls.count(('POST','/api/sendText'))==posts,'Restart/manual correction retransmitted uncertain body'
  print('AC14_PASS old publication_expired;missing publication_missing;conflict nointent;uncertain onePOST/oneattempt/sameintent/samebody across restart+manualrevision+contradictoryobservation; channel loopback only',flush=True)
 finally:resume_worker(worker)
print('CLEANUP owned scenario stopped --clean; no real WAHA',flush=True)
