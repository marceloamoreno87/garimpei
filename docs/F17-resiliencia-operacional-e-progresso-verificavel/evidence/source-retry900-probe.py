import datetime,hashlib,json,os,subprocess,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import parse_qs,urlsplit
from threading import Thread
from tests.factories.listing import Source,ControlledClock,PRODUCT
from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import configure,completed,sql,wait_for

ROOT=Path.cwd().parents[1];LAB=Path((ROOT/'.runtime/f18-owned-retry900-lab.path').read_text().strip())
ENV={k:v for k,v in os.environ.items() if not k.startswith('GARIMPEI_') and k not in {'DJANGO_SETTINGS_MODULE','VIRTUAL_ENV','DATABASE_URL','DJANGO_SECRET_KEY','POSTGRES_PASSWORD','WAHA_API_KEY'}}
REPORT={'feature':'F17','item':'WRK-RECOVERY-02','expected':'A real Retry-After900 source response is persisted; real reconcile_listings does not call the source before that deadline or report the waiting unit as stalled; the delay is not capped at300 and normal work resumes at the deadline','commands':[],'samples':[],'verdict':'BLOCKED','cleanup_succeeded':False}
START=time.monotonic()

def execute(command,cwd,env,label):
 t=time.monotonic();r=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True);(LAB/(label+'.private.log')).write_text(r.stdout+r.stderr);REPORT['commands'].append({'operation':label,'exit_code':r.returncode,'seconds':round(time.monotonic()-t,3)})
 if r.returncode:raise RuntimeError('Owned command failed; inspect private '+label)
 return r

def shell(instance,code,label):
 r=execute(['uv','run','--project','apps/backend','--frozen','--no-sync','python','apps/backend/manage.py','shell','-c',code],instance.root,ENV|{'GARIMPEI_ENV_FILE':str(instance.private_file),'PYTHONPATH':str(instance.root/'apps/backend/src')+':'+str(instance.root/'apps/backend')},label)
 return json.loads(r.stdout.strip().splitlines()[-1])

source=Source();responses=[]
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  parsed=urlsplit(self.path);params={k:v[0] for k,v in parse_qs(parsed.query,keep_blank_values=True).items()};status,body=source.respond(parsed.path,params);payload=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)))
  if status==429:self.send_header('Retry-After','900')
  self.end_headers();responses.append({'route':parsed.path,'status':status,'retry_after':900 if status==429 else None})
  try:self.wfile.write(payload)
  except (BrokenPipeError,ConnectionResetError):pass
 def log_message(self,*args):pass

EXTRACT='''
import json
from garimpei.main import reconcile_listings,build_operational_status,_listing_clock,_effective_listing_settings
from garimpei.infra.persistence.listing_models import CollectionState
for _ in range(3):reconcile_listings()
s=CollectionState.objects.get();clock=_listing_clock(_effective_listing_settings())();snapshot=build_operational_status().execute()
waiting=[x for x in snapshot['stages'] if x.get('stage')=='listing' and x.get('reason')=='source_rate_limit']
print(json.dumps({'clock':clock.isoformat(),'source_not_before':s.source_not_before.isoformat() if s.source_not_before else None,'next_attempt_at':s.next_attempt_at.isoformat() if s.next_attempt_at else None,'generation':s.generation,'source_wait_seconds':(s.source_not_before-clock).total_seconds() if s.source_not_before else None,'snapshot_id':snapshot['snapshot_id'],'rate_limited_units':waiting},default=str))
'''
prepared=False;server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 execute(['uv','run','--frozen','--no-sync','python','-m','tests.factories.operations_lab','prepare','--directory',str(LAB)],ROOT/'apps/backend',ENV,'prepare');prepared=True
 meta=json.loads((LAB/'lab.json').read_text())['instances'][0];instance=FoundationInstance(Path(meta['root']),Path(meta['file']))
 ENV['PYTHONPATH']=str(instance.root/'apps/backend/src')+':'+str(instance.root/'apps/backend');os.environ['PYTHONPATH']=ENV['PYTHONPATH']
 clock=ControlledClock(LAB/'clock',datetime.datetime.fromisoformat((LAB/'clock').read_text().strip()))
 with instance.private_file.open('a') as out:out.write(f'GARIMPEI_LISTING_FIXTURE_URL=http://127.0.0.1:{server.server_port}\nGARIMPEI_LISTING_FIXTURE_CLOCK={clock.path}\nGARIMPEI_LISTING_TIMEOUT=20\nGARIMPEI_LISTING_LEASE=60\nGARIMPEI_LISTING_RETRY_BASE=15\nGARIMPEI_LISTING_RETRY_MAX=300\nGARIMPEI_LISTING_INTERVAL=60\nGARIMPEI_OPERATIONS_ENABLED=true\n')
 execute(['./scripts/init.sh','--disposable'],instance.root,ENV|{'GARIMPEI_ENV_FILE':str(instance.private_file)},'init-source');configure(instance);completed(instance,1)
 source.mode='limited';clock.advance(61)
 wait_for(lambda:bool(sql(instance,"SELECT 1 FROM runtime_collectionstate WHERE source_not_before IS NOT NULL")),'source900deadline',seconds=25)
 wait_for(lambda:bool(sql(instance,"SELECT 1 FROM runtime_operationalunit WHERE stage='listing' AND reason='source_rate_limit'")),'operationalrate900',seconds=10)
 time.sleep(1)
 initial=shell(instance,EXTRACT,'initial900state');assert initial['source_wait_seconds']==900,initial['source_wait_seconds'];deadline=initial['source_not_before'];baseline_calls=len(source.calls);generation=initial['generation']
 REPORT['native_source_headers']=[r for r in responses if r['status']==429];REPORT['profile']={'source_timeout_seconds':20,'lease_seconds':60,'retry_base_seconds':15,'retry_max_seconds':300,'source_retry_after_seconds':900};REPORT['initial']=initial
 # The fake becomes healthy immediately; any premature request is observable.
 source.mode='initial'
 elapsed=0
 for offset in [0,179,180,301,600,899]:
  clock.advance(offset-elapsed);elapsed=offset
  observed=shell(instance,EXTRACT,'reconcile-before-deadline-'+str(offset));time.sleep(6 if offset==899 else 0.3)
  observed['elapsed_since_limit_seconds']=offset;observed['source_calls_since_limit']=len(source.calls)-baseline_calls;observed['deadline_preserved']=observed['source_not_before']==deadline and observed['next_attempt_at']==deadline;observed['generation_preserved']=observed['generation']==generation;observed['waiting_not_stalled']=bool(observed['rate_limited_units']) and all(x['state']=='waiting' and x['next_attempt_at'].replace(' ','T')==deadline for x in observed['rate_limited_units']);REPORT['samples'].append(observed)
 # Re-sample after background scheduler ticks at899, before advancing to900.
 end=shell(instance,EXTRACT,'background-before-deadline');REPORT['background_check']={'source_calls_since_limit':len(source.calls)-baseline_calls,'deadline_preserved':end['source_not_before']==deadline,'all_rate_limited_units_waiting':all(x['state']=='waiting' for x in end['rate_limited_units'])}
 clock.advance(1);at_due=shell(instance,EXTRACT,'reconcile-at-deadline');wait_for(lambda:len(source.calls)>baseline_calls,'source resumes only atdeadline',seconds=15);REPORT['at_deadline']={'elapsed_seconds':900,'source_calls_since_limit':len(source.calls)-baseline_calls,'reconciler_state':at_due}
 checks={'native_retry_after900_received':bool(REPORT['native_source_headers']),'no_calls_before_deadline':all(x['source_calls_since_limit']==0 for x in REPORT['samples']) and REPORT['background_check']['source_calls_since_limit']==0,'deadline_never_shortened':all(x['deadline_preserved'] for x in REPORT['samples']),'no_restart_or_generation_change_before_deadline':all(x['generation_preserved'] for x in REPORT['samples']),'wait_not_stalled_even_after180and300':all(x['waiting_not_stalled'] for x in REPORT['samples']),'resumed_at900':REPORT['at_deadline']['source_calls_since_limit']>0}
 REPORT['checks']=checks;REPORT['verdict']='PASS' if all(checks.values()) else 'FAIL'
finally:
 source.release.set();server.shutdown();thread.join();server.server_close()
 if prepared:
  try:execute(['uv','run','--frozen','--no-sync','python','-m','tests.factories.operations_lab','close','--directory',str(LAB)],ROOT/'apps/backend',ENV,'close');REPORT['cleanup_succeeded']=True
  except RuntimeError:pass
  inventory=json.loads((LAB/'fixture-manifest.json').read_text());REPORT['cleanup']=[{'state':x['state'],'processes':len(x['live_processes']),'containers':x['owned_containers'],'networks':x['owned_networks'],'volumes':x['owned_volumes']} for x in inventory['instances']]
  def digest(area):
   h=hashlib.sha256()
   for f in sorted(area.rglob('*.py')):h.update(str(f.relative_to(area)).encode());h.update(f.read_bytes())
   return h.hexdigest()
  REPORT['runtime_code_sha256']=digest(LAB/'checkout/apps/backend/src');REPORT['measurement_code_sha256']=digest(LAB/'checkout/apps/backend/tests')
 REPORT['seconds']=round(time.monotonic()-START,3);stamp=datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H-%M-%SZ');REPORT['at']=stamp
 p=ROOT/'docs/F17-resiliencia-operacional-e-progresso-verificavel/evidence'/('source-retry-after900-'+stamp+'.json');p.write_text(json.dumps(REPORT,indent=2)+'\n');print('PUBLIC_EVIDENCE='+str(p.relative_to(ROOT)),flush=True);print('VERDICT='+REPORT['verdict'],flush=True)
