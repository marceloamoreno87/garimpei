"""Failure telemetry survives real request persistence without keeping generated content."""

import pytest

from tests.factories.runtime import FoundationInstance
from tests.integration.test_media_persistence import media_instance as media_instance
from tests.integration.test_media_persistence import shell
from tests.integration.test_multimodal_condition import BOOT


@pytest.mark.parametrize(
    "fault,diagnostic",
    [
        ("json", "invalid_json_or_context"),
        ("schema", "schema_mismatch"),
        ("text", "text_reference_mismatch"),
        ("photo", "image_reference_mismatch"),
    ],
)
def test_response_rejection_keeps_timing_and_subreason_in_public_query(
    media_instance: tuple[FoundationInstance, str], fault: str, diagnostic: str
) -> None:
    instance, origin = media_instance
    output = shell(
        instance,
        origin,
        BOOT
        + "\nFAULT="
        + repr(fault)
        + "\nEXPECTED_DIAGNOSTIC="
        + repr(diagnostic)
        + """
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
original=ControlledEvidenceGateway.infer
def malformed(self,part,artifact):
 result=original(self,part,artifact)
 data=json.loads(result['content'])
 if FAULT=='schema':data['extra']='PRIVATE GENERATED CONTENT'
 if FAULT=='text':data['findings'][0]['references']=[dict(kind='text',field='description',quote='PRIVATE GENERATED CONTENT')]
 if FAULT=='photo':data['findings'][0]['references'][0]['sha256']='0'*64
 result['content']='PRIVATE INVALID JSON' if FAULT=='json' else json.dumps(data)
 result['metrics']=dict(total_duration=2000000000,load_duration=500000000,eval_duration=1200000000,prompt_eval_count=800,eval_count=200,size_vram=3000000000,context_length=4096,gpu_samples=[dict(scope='host',memory_mib=5000,utilization_percent=70)])
 return result
ControlledEvidenceGateway.infer=malformed
work=prepare.execute(listing.id)
assert run.execute() is False
response=PostgresInferenceQueries().analysis(work.requests[0])
part=response['parts'][0]
assert part['state']=='failed' and part['reason']=='invalid_output'
assert part['result'] is None
assert part['metrics']['diagnostic_code']==EXPECTED_DIAGNOSTIC,part
assert part['metrics']['total_duration']==2000000000 and part['metrics']['load_duration']==500000000
assert part['metrics']['size_vram']==3000000000 and part['metrics']['gpu_samples']
assert part['metrics']['sent'] is True and 'PRIVATE' not in json.dumps(part['metrics'])
assert complete.execute(work.id)
state=build_read_condition().execute(listing.id).state
assert state.assessment.reason=='invalid_analysis' and not state.satisfies_alert_condition
print('public failed query retains numeric telemetry and '+EXPECTED_DIAGNOSTIC+' without raw content or automatic promotion PASS')
""",
    )
    print(output)


@pytest.mark.parametrize("previous", ["condition-evidence-v1", "condition-evidence-v2"])
def test_persisted_previous_condition_profile_never_executes_as_legacy_f19(
    media_instance: tuple[FoundationInstance, str],
    previous: str,
) -> None:
    instance, origin = media_instance
    output = shell(
        instance,
        origin,
        BOOT
        + "\nPREVIOUS="
        + repr(previous)
        + "\n"
        + """
from garimpei.infra.persistence.inference_models import InferencePart
work=prepare.execute(listing.id)
for part in InferencePart.objects.filter(request_id__in=work.requests):
 part.content=dict(part.content,profile=PREVIOUS);part.save()
InferenceRequest.objects.filter(id__in=work.requests).update(prompt_version=PREVIOUS,schema_version=PREVIOUS)
before=gateway.calls
assert run.execute() is False
assert gateway.calls==before,'stale condition v1 reached inference/legacy validator'
part=InferencePart.objects.filter(request_id__in=work.requests).first()
assert part.state=='failed' and part.reason=='unsupported_prompt_or_schema'
assert part.metrics['sent'] is False and part.metrics['diagnostic_code']=='unsupported_profile'
print(PREVIOUS+' rejected before gateway, never treated as legacy F19 PASS')
""",
    )
    print(output)


@pytest.mark.parametrize("previous", ["condition-evidence-v1", "condition-evidence-v2"])
def test_current_profile_reanalysis_preserves_identified_previous_history(
    media_instance: tuple[FoundationInstance, str],
    previous: str,
) -> None:
    instance, origin = media_instance
    output = shell(
        instance,
        origin,
        BOOT
        + "\nPREVIOUS="
        + repr(previous)
        + "\n"
        + """
import hashlib
from garimpei.infra.persistence.inference_models import InferencePart
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
assert VERSION=='condition-evidence-v3'
first=prepare.execute(listing.id)
for _ in range(3):run.execute()
assert complete.execute(first.id)
row=ConditionAssessment.objects.get(id=first.id)
# A persisted legacy fixture represents the already previous release; it is never relabeled as the current profile.
old_fp=hashlib.sha256((first.value.fingerprint+PREVIOUS).encode()).hexdigest()
row.prompt_version=row.schema_version=PREVIOUS;row.input_fingerprint=old_fp
row.result=dict(row.result,fingerprint=old_fp);row.save()
AssessmentHead.objects.filter(listing=listing).update(input_fingerprint=old_fp)
InferenceRequest.objects.filter(id__in=first.requests).update(prompt_version=PREVIOUS,schema_version=PREVIOUS)
for part in InferencePart.objects.filter(request_id__in=first.requests):
 part.content=dict(part.content,profile=PREVIOUS);part.result=dict(part.result,schema_version=PREVIOUS);part.save()
historical=row.result;old_calls=gateway.calls
old=PostgresInferenceQueries().analysis(first.requests[0])
assert old['prompt_version']==old['schema_version']==PREVIOUS
assert old['parts'][0]['result']['schema_version']==PREVIOUS
current=build_read_condition().execute(listing.id).state
assert current.assessment.reason=='superseded_input' and current.assessment.previous==first.id
assert not current.satisfies_alert_condition
second=prepare.execute(listing.id)
assert second.id!=first.id and second.value.fingerprint!=old_fp and second.generation>first.generation
assert second.requests!=first.requests and gateway.calls==old_calls
new=PostgresInferenceQueries().analysis(second.requests[0])
assert new['prompt_version']==new['schema_version']==VERSION
assert ConditionAssessment.objects.get(id=second.id).result is None
for _ in range(3):run.execute()
assert complete.execute(second.id)
assert build_read_condition().execute(listing.id).state.satisfies_alert_condition
row.refresh_from_db();assert row.result==historical and row.prompt_version==PREVIOUS
assert PostgresInferenceQueries().analysis(first.requests[0])['prompt_version']==PREVIOUS
print(PREVIOUS+' history remains identified; v3 gets new fingerprint/generation/request without legacy/cache reuse PASS')
""",
    )
    print(output)


def test_accepted_http_envelope_then_rejected_json_persists_only_numeric_metrics(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    output = shell(
        instance,
        origin,
        BOOT
        + """
import tempfile
from uuid import uuid4
from pathlib import Path
from tests.factories.inference import inference_settings,serve_inference
from tests.unit.test_inference_failure_observability import MalformedOptionalMetricsFake
from garimpei.domain.inference.request import AnalysisInput
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
with tempfile.TemporaryDirectory() as temporary,serve_inference(MalformedOptionalMetricsFake('CANARY')) as endpoint:
 settings=inference_settings(Path(temporary),endpoint)
 guard=HostGpuGuard(settings.gpu_lock,settings.owner);assert guard.reserve()
 gateway=OllamaGateway(settings,guard,lambda:False)
 text=json.dumps(dict(text=dict(title='Controlado',description=None,condition=None)))
 part=PreparedPart('text',text,profile=VERSION)
 ticket=irepo.admit(AnalysisInput(obs.id,obs.ordinal,text,(),VERSION,VERSION,uuid4(),1),LocalInputPreparer(settings).artifact(),(part,))
 assert RunAnalysisUseCase(irepo,gateway,now).execute() is False
 public=PostgresInferenceQueries().analysis(ticket.request_id)['parts'][0]
 assert public['reason']=='invalid_output' and public['result'] is None
 metrics=public['metrics']
 assert metrics['diagnostic_code']=='invalid_json_or_context' and metrics['sent'] is True
 assert not {'total_duration','load_duration','context_length'} & metrics.keys(),metrics
 assert metrics['size_vram']==10 and metrics['eval_count']==40
 assert 'CANARY' not in json.dumps(metrics),metrics
print('real HTTP accepted envelope -> rejected condition JSON -> public PostgreSQL query omits malformed metrics without fabricating zero PASS')
""",
    )
    print(output)
