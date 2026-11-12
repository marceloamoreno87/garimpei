import os
import signal
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest

from tests.factories.runtime import FoundationInstance, pause_worker, prepare_instance


@pytest.fixture
def inference_instance(tmp_path: Path) -> Iterator[FoundationInstance]:
    root = Path(__file__).resolve().parents[4]
    instance = prepare_instance(root, tmp_path, "f19_" + uuid4().hex[:10])
    started = instance.command("./scripts/init.sh", "--disposable")
    assert started.returncode == 0, started.stdout + started.stderr
    try:
        yield instance
    finally:
        stopped = instance.command("./scripts/stop.sh", "--clean")
        assert stopped.returncode == 0, stopped.stdout + stopped.stderr


def run_assert(instance: FoundationInstance, script: str) -> None:
    group = pause_worker(instance)
    try:
        result = instance.shell(script)
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        os.killpg(group, signal.SIGCONT)


PREFIX = """
from datetime import timedelta
from django.utils.timezone import now
from garimpei.domain.inference.request import AnalysisInput
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
from garimpei.infra.persistence.inference_models import InferenceControl, InferenceRequest, InferencePart
from garimpei.infra.persistence.management.commands.local_ai import _smoke_observation
InferencePart.objects.all().delete()
InferenceRequest.objects.all().delete()
InferenceControl.objects.all().delete()
id,text=_smoke_observation('contract-test','text')
value=AnalysisInput(id,1,text,())
part=PreparedPart('text',text,coverage=({'kind':'text','provided':True,'sent':False,'examined':False},))
repo=PostgresInferenceRepository(lambda: 0,3)
ticket=repo.admit(value,'test-artifact',(part,))
point=now()
"""


def test_recovery_waits_for_proof_respects_due_and_three_attempts(
    inference_instance: FoundationInstance,
) -> None:
    run_assert(
        inference_instance,
        PREFIX
        + """
work=repo.claim(point)
assert work and repo.claim(point) is None
repo.failed(work,'timeout',point)
assert InferencePart.objects.get(pk=work.part_id).state=='running'
repo.recovered(False,point)
assert repo.claim(point+timedelta(seconds=500)) is None
repo.recovered(True,point)
assert repo.claim(point+timedelta(seconds=14)) is None
second=repo.claim(point+timedelta(seconds=16))
assert second and second.generation>work.generation
assert repo.publish(work,{}, {},point) is False
repo.failed(second,'execution_unknown',point)
repo.recovered(True,point)
assert repo.claim(point+timedelta(seconds=29)) is None
third=repo.claim(point+timedelta(seconds=31))
assert third
repo.failed(third,'timeout',point)
repo.recovered(True,point)
assert InferenceRequest.objects.get(pk=ticket.request_id).state=='failed'
assert InferencePart.objects.get(pk=work.part_id).attempts==3
assert repo.claim(point+timedelta(seconds=500)) is None
other_id,other_text=_smoke_observation('contract-test','unicode')
other=repo.admit(AnalysisInput(other_id,1,other_text,()),'test-artifact',(PreparedPart('text',other_text),))
assert repo.claim(point+timedelta(seconds=500)).request_id==other.request_id
""",
    )


def test_concurrent_admission_and_publication_are_idempotent(
    inference_instance: FoundationInstance,
) -> None:
    run_assert(
        inference_instance,
        PREFIX
        + """
from concurrent.futures import ThreadPoolExecutor
from django.db import connections

def request_one(_):
 try:
  return repo.admit(value,'test-artifact',(part,))
 finally:
  connections.close_all()
with ThreadPoolExecutor(max_workers=4) as pool:
 tickets=list(pool.map(request_one,range(4)))
assert all(t.request_id==ticket.request_id and t.reused for t in tickets)
assert InferenceRequest.objects.count()==1
work=repo.claim(point)
assert work
assert repo.publish(work,{'findings':[], 'unknowns':['Not examined beyond input'], 'limitations':[]},{},point)
assert repo.publish(work,{}, {},point) is False
result=PostgresInferenceQueries().analysis(ticket.request_id)
assert result['state']=='succeeded' and len(result['parts'])==1
assert result['coverage'][0]['sent'] and result['coverage'][0]['examined']
assert repo.admit(value,'test-artifact',(part,)).reused
""",
    )


def test_control_http_validates_csrf_conflict_and_unconfirmed_write(
    inference_instance: FoundationInstance,
) -> None:
    run_assert(
        inference_instance,
        PREFIX
        + """
from django.test import Client
from django.db import DatabaseError
from unittest.mock import patch
client=Client(enforce_csrf_checks=True,HTTP_HOST='127.0.0.1')
assert client.get('/integracoes/ia/').status_code==200
csrf=client.cookies['csrftoken'].value
assert client.post('/integracoes/ia/pausar/',{'revision':'1'}).status_code==403
assert client.post('/integracoes/ia/pausar/',{'revision':'x','csrfmiddlewaretoken':csrf}).status_code==400
assert client.post('/integracoes/ia/pausar/',{'revision':'1','csrfmiddlewaretoken':csrf}).status_code==303
assert InferenceControl.objects.get(pk=1).paused
assert client.post('/integracoes/ia/pausar/',{'revision':'1','csrfmiddlewaretoken':csrf}).status_code==303
assert client.post('/integracoes/ia/retomar/',{'revision':'1','csrfmiddlewaretoken':csrf}).status_code==409
revision=InferenceControl.objects.get(pk=1).revision
with patch.object(PostgresInferenceRepository,'control',side_effect=DatabaseError):
 assert client.post('/integracoes/ia/retomar/',{'revision':str(revision),'csrfmiddlewaretoken':csrf}).status_code==503
assert InferenceControl.objects.get(pk=1).paused
assert client.post('/integracoes/ia/retomar/',{'revision':str(revision),'csrfmiddlewaretoken':csrf}).status_code==303
assert InferenceControl.objects.get(pk=1).reason!='paused'
""",
    )


def test_retry_success_clears_obsolete_diagnostic(inference_instance: FoundationInstance) -> None:
    run_assert(
        inference_instance,
        PREFIX
        + """
work=repo.claim(point)
repo.failed(work,'service_unavailable',point)
retry=repo.claim(point+timedelta(seconds=16))
assert retry
assert repo.publish(retry,{'findings':[], 'unknowns':[], 'limitations':[]},{},point)
part=InferencePart.objects.get(pk=retry.part_id)
assert part.state=='succeeded' and part.reason==''
""",
    )


def test_pause_during_call_finishes_one_part_and_requires_explicit_resume(
    inference_instance: FoundationInstance,
) -> None:
    run_assert(
        inference_instance,
        PREFIX
        + """
import json
from dataclasses import asdict
from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase
InferencePart.objects.create(request_id=ticket.request_id,position=1,content=asdict(PreparedPart('second',text)))
class PauseDuringInferenceGatewayFake:
 calls=0
 def infer(self,part,artifact):
  self.calls+=1
  if self.calls==1: repo.control(True,1)
  return {'content':json.dumps({'findings':[], 'unknowns':['No independent confirmation'], 'limitations':[]}), 'metrics':{}}
fake=PauseDuringInferenceGatewayFake()
run=RunAnalysisUseCase(repo,fake,lambda:point)
assert run.execute() and fake.calls==1
assert InferenceControl.objects.get(pk=1).paused
assert InferenceRequest.objects.get(pk=ticket.request_id).state=='pending'
assert not run.execute() and fake.calls==1
repo.control(False,2)
assert run.execute() and fake.calls==2
assert InferenceRequest.objects.get(pk=ticket.request_id).state=='succeeded'
""",
    )


def test_empty_queue_reconciliation_does_not_enqueue_work(
    inference_instance: FoundationInstance,
) -> None:
    run_assert(
        inference_instance,
        """
from django.utils.timezone import now
from datetime import timedelta
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.persistence.management.commands.local_ai import _smoke_observation
from garimpei.infra.persistence.inference_models import InferenceRequest
from garimpei.domain.inference.request import AnalysisInput
from garimpei.domain.inference.ports import PreparedPart
calls=[]
def enqueue():
 calls.append('inference')
 return 0
repo=PostgresInferenceRepository(enqueue,100)
point=now()
repo.reconcile(point)
assert calls==[] and InferenceRequest.objects.count()==0
identity,text=_smoke_observation('reconcile-no-empty','text')
ticket=repo.admit(AnalysisInput(identity,1,text,()),'controlled-artifact',(PreparedPart('text',text),))
assert len(calls)==1
InferenceRequest.objects.filter(pk=ticket.request_id).update(state='awaiting_resource',next_attempt_at=point+timedelta(seconds=15))
repo.reconcile(point)
assert len(calls)==1
repo.reconcile(point+timedelta(seconds=16))
assert len(calls)==2
""",
    )


def test_uncertain_execution_renders_cause_before_active_claim(
    inference_instance: FoundationInstance,
) -> None:
    run_assert(
        inference_instance,
        PREFIX
        + """
from django.test import Client
client=Client(HTTP_HOST='127.0.0.1')
work=repo.claim(point)
assert work
repo.failed(work,'timeout',point,sent=True)
InferenceControl.objects.filter(pk=1).update(service=True,resident=False)
body=client.get('/integracoes/ia/').content.decode()
assert 'A análise excedeu o prazo' in body
assert 'Encerramento ainda não confirmado' in body
assert 'Residência ainda não confirmada' in body
assert 'Analisando localmente' not in body
assert 'Modelo não residente na última verificação' not in body
repo.control(True,1)
body=client.get('/integracoes/ia/').content.decode()
assert 'A análise excedeu o prazo' in body and 'Retomar IA' in body
repo.recovered(True,point)
repo.control(False,2)
retry=repo.claim(point+timedelta(seconds=16))
assert retry
repo.failed(retry,'execution_unknown',point,sent=True)
body=client.get('/integracoes/ia/').content.decode()
assert 'Conferindo a chamada anterior' in body
assert 'Encerramento ainda não confirmado' in body
assert 'Analisando localmente' not in body
""",
    )
