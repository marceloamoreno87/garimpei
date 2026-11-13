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


def test_persisted_condition_v1_is_never_executed_or_accepted_as_legacy_f19(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    output = shell(
        instance,
        origin,
        BOOT
        + """
from garimpei.infra.persistence.inference_models import InferencePart
work=prepare.execute(listing.id)
for part in InferencePart.objects.filter(request_id__in=work.requests):
 part.content=dict(part.content,profile='condition-evidence-v1');part.save()
InferenceRequest.objects.filter(id__in=work.requests).update(prompt_version='condition-evidence-v1',schema_version='condition-evidence-v1')
before=gateway.calls
assert run.execute() is False
assert gateway.calls==before,'stale condition v1 reached inference/legacy validator'
part=InferencePart.objects.filter(request_id__in=work.requests).first()
assert part.state=='failed' and part.reason=='unsupported_prompt_or_schema'
assert part.metrics['sent'] is False and part.metrics['diagnostic_code']=='unsupported_profile'
print('persisted condition-evidence-v1 is rejected before gateway and never treated as legacy F19 PASS')
""",
    )
    print(output)


def test_current_v2_reanalysis_preserves_identified_v1_history_and_uses_new_request(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    output = shell(
        instance,
        origin,
        BOOT
        + """
import hashlib
from garimpei.infra.persistence.inference_models import InferencePart
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
assert VERSION=='condition-evidence-v2'
first=prepare.execute(listing.id)
for _ in range(3):run.execute()
assert complete.execute(first.id)
row=ConditionAssessment.objects.get(id=first.id)
# A persisted legacy fixture represents the already confirmed v1 release; it is never relabeled v2.
old_fp=hashlib.sha256((first.value.fingerprint+'condition-evidence-v1').encode()).hexdigest()
row.prompt_version=row.schema_version='condition-evidence-v1';row.input_fingerprint=old_fp
row.result=dict(row.result,fingerprint=old_fp);row.save()
AssessmentHead.objects.filter(listing=listing).update(input_fingerprint=old_fp)
InferenceRequest.objects.filter(id__in=first.requests).update(prompt_version='condition-evidence-v1',schema_version='condition-evidence-v1')
for part in InferencePart.objects.filter(request_id__in=first.requests):
 part.content=dict(part.content,profile='condition-evidence-v1');part.result=dict(part.result,schema_version='condition-evidence-v1');part.save()
historical=row.result;old_calls=gateway.calls
old=PostgresInferenceQueries().analysis(first.requests[0])
assert old['prompt_version']==old['schema_version']=='condition-evidence-v1'
assert old['parts'][0]['result']['schema_version']=='condition-evidence-v1'
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
row.refresh_from_db();assert row.result==historical and row.prompt_version=='condition-evidence-v1'
assert PostgresInferenceQueries().analysis(first.requests[0])['prompt_version']=='condition-evidence-v1'
print('historical prompt/schema=condition-evidence-v1 remains identified; current condition-evidence-v2 gets new fingerprint/generation/request without legacy/cache reuse PASS')
""",
    )
    print(output)
