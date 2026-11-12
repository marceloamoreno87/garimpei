"""PostgreSQL composition with named F19 fakes; does not assert GPU or model quality."""

from tests.factories.runtime import FoundationInstance
from tests.integration.test_media_persistence import media_instance as media_instance
from tests.integration.test_media_persistence import shell

BOOT = """
import json,os
from dataclasses import replace
from garimpei.domain.inference.condition_evidence import VERSION
from garimpei.domain.inference.ports import PreparedPart
from garimpei.domain.inference.result import AnalysisResult
from garimpei.infra.persistence.inference_models import InferenceControl,InferenceRequest
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.gateway.inference.registry import registered
from garimpei.infra.gateway.inference.input_preparer import artifact_signature,read_lock
from garimpei.config.env import load_inference_settings
from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase
from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase
from garimpei.infra.gateway.listing.assessment_inputs import LocalAssessmentInputs
from garimpei.infra.gateway.listing.assessment_inference import LocalAssessmentInference
from garimpei.infra.repository.listing.assessment_repository import PostgresAssessmentRepository
from garimpei.infra.persistence.assessment_models import ConditionAssessment,AssessmentHead
from garimpei.usecase.listing.prepare_assessment_usecase import PrepareAssessmentUseCase
from garimpei.usecase.listing.complete_assessment_usecase import CompleteAssessmentUseCase
from garimpei.main import build_read_condition,build_read_monitoring_configuration,build_publish_exploration
from tests.factories.monitoring import prepare_state
from garimpei.domain.listing.scope import Scope
os.environ['GARIMPEI_ASSESSMENT_ENABLED']='true'
InferenceControl.objects.all().delete()
prepare_state('ATIVA')
listing=Listing.objects.get(id=a['listing']);obs=listing.latest
obs.evidence=dict(obs.evidence,title='Notebook Dell',description='O aparelho funciona perfeitamente.')
config=build_read_monitoring_configuration().execute();scope=Scope.from_snapshot(config)
obs.cycle.scope_key=scope.key;obs.cycle.save()
obs.cycle.state.configuration_id=scope.configuration_id;obs.cycle.state.save()
obs.coverage=dict(pickup='confirmed',shipping='unknown',distance_km=None,pickup_reason='within_radius',shipping_reason='not_offered');obs.save()
ListingObservation.objects.exclude(id=obs.id).update(coverage=obs.coverage)
class ControlledEvidencePreparer:
 def artifact(self):return artifact_signature(read_lock(load_inference_settings().model_lock))
 def prepare(self,value):
  parts=[PreparedPart('text',value.text,model_digest=read_lock(load_inference_settings().model_lock)['model_digest'],profile=VERSION)]
  for image in value.images:
   meta=registered(load_inference_settings(),image.id)
   parts.append(PreparedPart('image-'+image.id,value.text,image.id,image.sha256,(dict(kind='image',id=image.id,sha256=image.sha256,source_sha256=meta['source_sha256']),),profile=VERSION))
  return tuple(part for part in parts if part.image_id is not None) if value.images else tuple(parts)
class ControlledEvidenceGateway:
 kind='light_wear';calls=0;fault=None
 def infer(self,part,artifact):
  self.calls+=1
  if self.fault:raise self.fault
  result=dict(schema_version=VERSION,findings=[],conflicts=[],limitations=['Portas precisam de teste presencial'],examined_photos=[],omitted_photos=[])
  if part.image_id:
   original=part.coverage[0]['source_sha256']
   result['findings']=[dict(dimension='appearance',assessment=self.kind,description='Sinal visual controlado',references=[dict(kind='image',photo_id=part.image_id,sha256=original)])]
   result['examined_photos']=[dict(photo_id=part.image_id,sha256=original)]
  return dict(content=json.dumps(result),metrics=dict(controlled_fake=True))
irepo=PostgresInferenceRepository(lambda:0,100)
gateway=ControlledEvidenceGateway()
inference=LocalAssessmentInference(RequestAnalysisUseCase(irepo,ControlledEvidencePreparer()),build_media_repository(),build_media_store(),queries)
repository=PostgresAssessmentRepository();inputs=LocalAssessmentInputs()
prepare=PrepareAssessmentUseCase(inputs,repository,inference,now)
complete=CompleteAssessmentUseCase(repository,inference,now)
run=RunAnalysisUseCase(irepo,gateway,now)
"""


def test_pending_then_sufficient_evidence_is_shared_and_pinned(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + """
initial=build_read_condition().execute(listing.id).state
assert initial.effective=='uncertain' and not initial.satisfies_alert_condition
work=prepare.execute(listing.id)
assert len(work.pins)==2 and len(work.requests)==1
assert build_read_condition().execute(listing.id).state.assessment.status=='waiting'
for _ in range(3):run.execute()
assert complete.execute(work.id)
state=build_read_condition().execute(listing.id).state
assert state.analysis.condition=='good' and state.assessment.sufficient and state.satisfies_alert_condition
assert state.assessment.observation_id==obs.id and len(state.assessment.photo_coverage)==2
assert len({r.sha256 for f in state.assessment.findings for r in f.references})==2
before=gateway.calls;again=prepare.execute(listing.id)
assert again.id==work.id and gateway.calls==before
assert not complete.execute(work.id)
assert ConditionAssessment.objects.get(id=work.id).publication_order is not None
assert MediaReference.objects.filter(consumer='condition-assessment',released_at=None).count()==2
print('pending -> sufficient; F14 exact source hashes/pins; one publication and idempotent requests PASS')
""",
    )


def test_late_result_and_manual_choice_survive_new_input(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + """
from garimpei.main import build_classify_condition
state=build_read_condition().execute(listing.id).state
build_classify_condition().execute(listing.id,'good',state.revision)
first=prepare.execute(listing.id)
for _ in range(3):run.execute()
assert complete.execute(first.id)
old=ConditionAssessment.objects.get(id=first.id)
obs.evidence=dict(obs.evidence,description='O aparelho não liga.');obs.save()
second=prepare.execute(listing.id)
assert second.id!=first.id
assert build_read_condition().execute(listing.id).state.manual=='good'
for _ in range(3):run.execute()
assert complete.execute(second.id)
current=build_read_condition().execute(listing.id).state
assert current.manual=='good' and current.analysis.condition=='defect' and current.conflict
assert not repository.publish(first,replace(current.assessment,condition='good'),now())
assert AssessmentHead.objects.get(listing=listing).current_id==second.id
assert ConditionAssessment.objects.get(id=first.id).result==old.result
print('new text/version and manual precedence preserve historical result, late publication is fenced PASS')
""",
    )


def test_stale_input_is_blocked_before_next_worker_reconcile(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + """
from garimpei.infra.repository.alert.first_inputs import automatic_signature
os.environ['GARIMPEI_ASSESSMENT_ENABLED']='false';baseline=automatic_signature(listing)
os.environ['GARIMPEI_ASSESSMENT_ENABLED']='true'
assert automatic_signature(listing)==baseline
first=prepare.execute(listing.id)
for _ in range(3):run.execute()
obs.evidence=dict(obs.evidence,description='Não foi testado. Funciona perfeitamente.');obs.save()
state=build_read_condition().execute(listing.id).state
assert state.analysis.condition=='uncertain' and not state.satisfies_alert_condition
assert not complete.execute(first.id)
assert ConditionAssessment.objects.get(id=first.id).status=='superseded'
from garimpei.infra.persistence.alert_models import AlertIntent
assert not AlertIntent.objects.exists()
print('activation preserves pre-F15 signature; changed text blocks old output before next reconciliation PASS')
""",
    )


def test_concurrent_preparation_converges_and_reobservation_reuses_result(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + """
from concurrent.futures import ThreadPoolExecutor
from django.db import connections
from garimpei.domain.media.media import Manifest,Photo,Variant
from garimpei.infra.repository.media.captures import create_capture
from garimpei.config.env import load_media_settings
from garimpei.infra.persistence.listing_models import CollectionCycle

def concurrent():
 try:return prepare.execute(listing.id)
 finally:connections.close_all()
with ThreadPoolExecutor(2) as pool:works=list(pool.map(lambda _:concurrent(),range(2)))
assert works[0].id==works[1].id
assert ConditionAssessment.objects.count()==1 and InferenceRequest.objects.count()==1
for _ in range(3):run.execute()
assert complete.execute(works[0].id)
before=gateway.calls
first=ConditionAssessment.objects.get(id=works[0].id)
cycle=CollectionCycle.objects.create(state=obs.cycle.state,scope_key=obs.cycle.scope_key,revision=obs.cycle.revision)
new=ListingObservation.objects.create(listing=listing,cycle=cycle,ordinal=obs.ordinal+1,observed_at=now(),price=obs.price,evidence=obs.evidence,coverage=obs.coverage)
listing.latest=new;listing.ordinal=new.ordinal;listing.save()
old_capture=MediaCapture.objects.get(observation=obs)
photos=tuple(Photo(e.photo_key,tuple(Variant(**v) for v in e.candidates),e.primary) for e in old_capture.entries.order_by('position'))
create_capture(new,Manifest('present',photos,True,''),load_media_settings().policy,now())
for _ in range(4):
 for job in build_media_repository().due(now()):runner.execute(job)
again=prepare.execute(listing.id)
assert again.id!=works[0].id and again.requests==works[0].requests
assert complete.execute(again.id) and gateway.calls==before
state=build_read_condition().execute(listing.id).state
assert state.assessment.observation_id==new.id and state.assessment.sufficient
assert ConditionAssessment.objects.get(id=again.id).reason=='seller_declared_visual_assessment'
print('concurrent input -> one request; equal content -> explicit new observation link without new model inference PASS')
""",
    )


def test_failed_inference_keeps_history_and_http_read_does_not_wait(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + """
from django.test import Client
from unittest.mock import patch
from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.persistence.inference_models import InferencePart
first=prepare.execute(listing.id)
for _ in range(3):run.execute()
assert complete.execute(first.id)
obs.evidence=dict(obs.evidence,description='O aparelho funciona perfeitamente. Caixa incluída.');obs.save()
second=prepare.execute(listing.id)
gateway.fault=InferenceError('out_of_memory')
for _ in range(3):
 InferenceRequest.objects.filter(id__in=second.requests).update(next_attempt_at=now())
 run.execute()
assert complete.execute(second.id)
assert InferencePart.objects.filter(request_id__in=second.requests).values_list('attempts',flat=True).first()==3
state=build_read_condition().execute(listing.id).state
assert state.assessment.status=='failed' and state.assessment.reason=='gpu_resource_unavailable'
assert state.assessment.previous==first.id and not state.satisfies_alert_condition
assert ConditionAssessment.objects.get(id=first.id).condition=='good'
build_publish_exploration().execute()
client=Client(HTTP_HOST='127.0.0.1')
with patch('garimpei.infra.gateway.inference.ollama_gateway.OllamaGateway.infer',side_effect=AssertionError('HTTP performed inference')):
 response=client.get('/ofertas/'+str(listing.id)+'/')
assert response.status_code==200 and 'Recursos locais de IA indisponíveis'.encode() in response.content
assert str(first.id).encode() in response.content and b'Notebook Dell' in response.content
print('F19 three bounded failures, prior confirmed history, HTTP200 honest failure and no inline inference PASS')
""",
    )


def test_manual_csrf_revision_and_conflict_still_use_existing_form(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + """
from django.test import Client,RequestFactory
from django.middleware.csrf import get_token
from garimpei.infra.persistence.alert_models import AlertIntent,AlertAttempt
client=Client(HTTP_HOST='127.0.0.1',enforce_csrf_checks=True)
path='/ofertas/'+str(listing.id)+'/condicao/'
assert client.post(path,dict(choice='good',revision='0')).status_code==403
request=RequestFactory().get('/');token=get_token(request)
client.cookies['csrftoken']=request.META['CSRF_COOKIE']
valid=dict(choice='good',revision='0',csrfmiddlewaretoken=token)
response=client.post(path,valid)
assert response.status_code==303
assert client.post(path,dict(valid,choice='defect')).status_code==409
state=build_read_condition().execute(listing.id).state
assert state.manual=='good' and state.revision==1 and not state.satisfies_alert_condition
assert not AlertIntent.objects.exists() and not AlertAttempt.objects.exists()
print('manual form CSRF/303/409 preserves chosen tab without manufacturing sufficient analysis or intent PASS')
""",
    )
