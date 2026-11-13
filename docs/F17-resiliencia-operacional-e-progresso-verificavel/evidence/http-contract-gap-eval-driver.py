import datetime
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4

ROOT=Path.cwd()
LAB=Path(ROOT.joinpath('.runtime/f18-owned-http-lab.path').read_text().strip())
ENV={k:v for k,v in os.environ.items() if not k.startswith('GARIMPEI_') and k not in {'DJANGO_SETTINGS_MODULE','VIRTUAL_ENV','DATABASE_URL','DJANGO_SECRET_KEY','POSTGRES_PASSWORD','WAHA_API_KEY'}}
COMMANDS=[]
RESULTS=[]

def lifecycle(operation,extra=()):
    started=time.monotonic()
    command=['uv','run','--frozen','--no-sync','python','-m','tests.factories.operations_lab',operation,'--directory',str(LAB),*extra]
    result=subprocess.run(command,cwd=ROOT/'apps/backend',env=ENV,capture_output=True,text=True)
    (LAB/(operation+'.private.log')).write_text(result.stdout+result.stderr)
    row=dict(operation=operation,arguments=list(extra),exit_code=result.returncode,seconds=round(time.monotonic()-started,3));COMMANDS.append(row);print(json.dumps(row),flush=True)
    return result.returncode

def shell(code):
    data=json.loads((LAB/'lab.json').read_text())['instances'][0]
    env=ENV|{'GARIMPEI_ENV_FILE':data['file']}
    result=subprocess.run(['uv','run','--project','apps/backend','--frozen','--no-sync','python','apps/backend/manage.py','shell','-c',code],cwd=data['root'],env=env,capture_output=True,text=True)
    if result.returncode:
        (LAB/'shell-failure.private.log').write_text(result.stdout+result.stderr)
        raise RuntimeError('Owned evaluation setup/snapshot failed; inspect private log')
    return json.loads(result.stdout.strip().splitlines()[-1])

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

JAR=http.cookiejar.CookieJar()
CLIENT=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR),NoRedirect())
BASE=''

def request(path,data=None):
    payload=None if data is None else urllib.parse.urlencode(data).encode()
    req=urllib.request.Request(BASE+path,data=payload)
    try:response=CLIENT.open(req,timeout=15)
    except urllib.error.HTTPError as error:response=error
    with response:
        return response.status,dict(response.headers),response.read()

def snapshot(identity):
    return shell("import json;from garimpei.infra.persistence.operations_models import OperationalUnit,RecoveryBarrier;from garimpei.infra.persistence.alert_models import AlertFeedCursor;print(json.dumps({'unit':OperationalUnit.objects.filter(id="+repr(identity)+").values().get(),'barriers':list(RecoveryBarrier.objects.values('installation','state')),'dispatch':list(AlertFeedCursor.objects.values_list('dispatch_suspended',flat=True))},default=str,sort_keys=True))")

def response_public(response):
    status,headers,body=response
    return dict(status=status,headers={k:v for k,v in headers.items() if k.lower() in {'cache-control','content-disposition','content-length','content-type','etag'}},body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest())

def add(item,expected,observed,passed):
    RESULTS.append(dict(item=item,verdict='PASS' if passed else 'FAIL',expected=expected,observed=observed))
    print(item,RESULTS[-1]['verdict'],flush=True)

prepared=False
ok=False
try:
    for op,args in [('prepare',()),('start',()),('seed',('--scenario','recovery'))]:
        if lifecycle(op,args):raise RuntimeError('Owned lifecycle precondition failed')
        if op=='prepare':prepared=True
    setup=shell('''
import json
from uuid import uuid4
from django.utils.timezone import now
from garimpei.config.env import load_config,load_operations_settings
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.operations_models import BackupRecord,OperationalUnit
from garimpei.infra.repository.operations.progress_repository import PostgresOperationalRepository
r=build_backup_repository();copy=r.create();assert copy
export=r.export(copy,uuid4());record=BackupRecord.objects.get(id=export)
partial=BackupRecord.objects.create(id=uuid4(),installation=load_config().environment_id,kind='export',source_id=copy,started_at=now(),state='creating')
foreign=BackupRecord.objects.create(id=uuid4(),installation='eval_synthetic_foreign',kind='export',source_id=copy,started_at=now(),state='completed',finished_at=now(),file_key=record.file_key,size=record.size,sha256=record.sha256)
store=PostgresOperationalRepository(load_config().environment_id,now)
units={}
for label in ['stale','auth','barrier','csrf']:
 store.confirm('valuation','http-evaluation-'+label,7,'confirmed-checkpoint-'+label,now(),pending=1)
 if label=='auth':store.failure('valuation','http-evaluation-'+label,7,'access_denied',now())
 else:
  for _ in range(3):store.failure('valuation','http-evaluation-'+label,7,'valuation_publication_failed',now())
 units[label]=str(OperationalUnit.objects.get(scope='http-evaluation-'+label).id)
print(json.dumps(dict(export=str(export),partial=str(partial.id),foreign=str(foreign.id),sha256=record.sha256,size=record.size,units=units,copy=str(copy))))
''')
    source=json.loads((LAB/'lab.json').read_text())['instances'][0]
    import_path="import json;from garimpei.config.env import load_config;print(json.dumps({'port':load_config().web_port}))"
    BASE='http://127.0.0.1:'+str(shell(import_path)['port'])
    code,headers,body=request('/configuracoes/')
    assert code==200
    token=next(cookie.value for cookie in JAR if cookie.name=='csrftoken')
    # HTTP API order follows the contract: resume, then exports.
    route='/acompanhamento/etapas/valuation/retomar/'
    variants=[]
    for label,revision in [('stale','6'),('auth','7')]:
        before=snapshot(setup['units'][label])
        response=request(route,dict(unidade=setup['units'][label],revisao=revision,csrfmiddlewaretoken=token))
        after=snapshot(setup['units'][label])
        alert=re.search(rb'<div role="alert"[^>]*>(.*?)</div>',response[2],re.S)
        alert_text=re.sub('<[^>]*>',' ',alert[1].decode()) if alert else response[2].decode()
        alert_text=' '.join(alert_text.split())
        specific=bool(re.search(r'revis[aã]o|acesso|autentic',alert_text,re.I))
        variants.append(dict(case=label,**response_public(response),state_preserved=before==after,specific_reason=specific,alert=alert_text))
    shell("import json;from uuid import UUID;from django.utils.timezone import now;from garimpei.config.env import load_config;from garimpei.infra.persistence.operations_models import RecoveryBarrier;from garimpei.infra.persistence.alert_models import AlertFeedCursor;RecoveryBarrier.objects.create(installation=load_config().environment_id,backup_id=UUID("+repr(setup['copy'])+"),snapshot_at=now(),restored_at=now(),state='blocked');AlertFeedCursor.objects.update(dispatch_suspended=True);print(json.dumps({'prepared':True}))")
    before=snapshot(setup['units']['barrier'])
    response=request(route,dict(unidade=setup['units']['barrier'],revisao='7',csrfmiddlewaretoken=token))
    after=snapshot(setup['units']['barrier'])
    variants.append(dict(case='barrier',**response_public(response),state_preserved=before==after,specific_reason=b'reconciliar' in response[2],dispatch_suspended=all(after['dispatch'])))
    add('API-RESUME-02','Each obsolete revision, authentication suspension and recovery barrier returns409 with specific recoverable reason; checkpoint/budget/suspension/dispatch unchanged',variants,all(x['status']==409 and x['state_preserved'] and x['specific_reason'] for x in variants))
    before=snapshot(setup['units']['csrf'])
    response=request(route,dict(unidade=setup['units']['csrf'],revisao='7'))
    after=snapshot(setup['units']['csrf'])
    add('API-RESUME-03','Missing CSRF returns403 without budget/checkpoint mutation',dict(**response_public(response),state_preserved=before==after),response[0]==403 and before==after)
    response=request(f"/acompanhamento/exportacoes/{setup['partial']}/arquivo/")
    add('API-EXPORT-02','Incomplete export returns409 without partial archive body or completed state',dict(**response_public(response),archive_content_type=response[1].get('Content-Type','').startswith('application/gzip')),response[0]==409 and not response[2].startswith(b'\x1f\x8b'))
    response=request(f"/acompanhamento/exportacoes/{setup['export']}/arquivo/")
    digest=hashlib.sha256(response[2]).hexdigest()
    public=response_public(response)|dict(checksum_matches_registered=digest==setup['sha256'],bytes_match_registered=len(response[2])==setup['size'])
    add('API-EXPORT-03','Completed export returns200 attachment/no-store with all bytes and registered checksum',public,response[0]==200 and 'attachment' in response[1].get('Content-Disposition','') and response[1].get('Cache-Control')=='no-store' and digest==setup['sha256'] and len(response[2])==setup['size'])
    unknown=[]
    for label,identity in [('unknown',str(uuid4())),('foreign_installation',setup['foreign'])]:
        response=request(f'/acompanhamento/exportacoes/{identity}/arquivo/')
        unknown.append(dict(case=label,**response_public(response),private_path_leaked=str(LAB).encode() in response[2] or source['root'].encode() in response[2]))
    add('API-EXPORT-04','Unknown and foreign-installation UUIDs return404 without private path or arbitrary file bytes',unknown,all(x['status']==404 and not x['private_path_leaked'] for x in unknown))
    ok=True
finally:
    closed=lifecycle('close')==0 if prepared else False
    if prepared:
        inventory=json.loads((LAB/'fixture-manifest.json').read_text())
        cleanup=[dict(state=x['state'],live_process_count=len(x['live_processes']),owned_containers=x['owned_containers'],owned_networks=x['owned_networks'],owned_volumes=x['owned_volumes']) for x in inventory['instances']]
    else:cleanup=[]
    stamp=datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H-%M-%SZ')
    report=dict(feature='F17',scope='Partial HTTP evaluation only; no product/source/test changes',measured_at=stamp,completed=ok,commands=COMMANDS,items=RESULTS,cleanup=cleanup,cleanup_succeeded=closed)
    (LAB/'public-http-report.json').write_text(json.dumps(report,indent=2)+'\n')
    output=ROOT/'docs/F17-resiliencia-operacional-e-progresso-verificavel/evidence'/('http-contract-gap-eval-'+stamp+'.json')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print('PUBLIC_EVIDENCE='+str(output.relative_to(ROOT)),flush=True)
raise SystemExit(0 if ok and closed else 1)
