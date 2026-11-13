"""Local consumers use real PostgreSQL; named preparer avoids claiming a model call."""

from tests.factories.runtime import FoundationInstance
from tests.integration.test_inference import run_assert

SCRIPT = r"""
import json
from uuid import uuid4
from unittest.mock import patch
from django.test import Client
from django.utils.timezone import now
from garimpei.domain.assistance.errors import AssistanceError
from garimpei.domain.assistance.review import ReviewCommand, validate_assistance_output
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.persistence.assistance_models import AssistanceReview, AssistanceOperationsSnapshot
from garimpei.infra.persistence.listing_models import ListingObservation
from garimpei.infra.persistence.operations_models import OperationalUnit
from garimpei.infra.persistence.identity_models import IdentityProgress
from tests.factories.assistance import seed_observation
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.repository.assistance.postgres_repository import PostgresAssistanceRepository
from garimpei.infra.repository.assistance.operations import capture_operations_snapshot
from garimpei.infra.repository.valuation.identity_repository import PostgresIdentityRepository
from garimpei.infra.queries.assistance.postgres_queries import PostgresAssistanceQueries
from garimpei.infra.http.assistance.review_handler import AssistanceHandler
from garimpei.usecase.assistance.request_review_usecase import RequestReviewUseCase
from garimpei.usecase.assistance.read_reviews_usecase import ReadReviewsUseCase
from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase

class NamedFinitePreparer:
 def artifact(self): return 'controlled-assistance-artifact'
 def prepare(self, value): return (PreparedPart('text',value.text,profile=value.prompt_version),)

observation_id,_=seed_observation('f23-consumer-test','text')
observation=ListingObservation.objects.select_related('listing').get(pk=observation_id)
observation.evidence=dict(observation.evidence,title='PlayStation 5 Slim Digital 825GB',description='Usado. Funcionando perfeitamente.',condition='Usado — seminovo',source_available=True)
observation.save(update_fields=['evidence'])
PostgresIdentityRepository(now)._record(observation.listing_id)
inference=PostgresInferenceRepository(lambda:0,100)
requested=[]
repository=PostgresAssistanceRepository(RequestAnalysisUseCase(inference,NamedFinitePreparer()),lambda:requested.append('condition'))
command=ReviewCommand(uuid4(),'identity',observation.listing_id,observation.ordinal)
ticket=repository.admit(command)
assert repository.admit(command).id==ticket.id
assert AssistanceReview.objects.filter(pk=ticket.id).count()==1
try:
 repository.admit(ReviewCommand(command.command_id,'condition',observation.listing_id,observation.ordinal))
 raise AssertionError('command collision accepted')
except AssistanceError as error:
 assert error.status==409
try:
 repository.admit(ReviewCommand(uuid4(),'identity',observation.listing_id,observation.ordinal+1))
 raise AssertionError('stale revision accepted')
except AssistanceError as error:
 assert error.status==409
review=AssistanceReview.objects.get(pk=ticket.id)
facts=review.input_snapshot['facts']
assert facts
findings=[dict(field=f['field'],value=f['value'],evidence_refs=[f['id']],reason_code='explicit_evidence') for f in facts]
payload=dict(outcome='supported',findings=findings,limitations=[])
work=inference.claim(now()); assert work
validated=validate_assistance_output('identity-review-v1',json.dumps(payload),work.part.text)
assert inference.publish(work,validated,{'controlled_fake':True},now())
repository.reconcile()
review.refresh_from_db(); assert review.state=='supported'
assert any(c['kind']=='normalization' for c in review.consumed_by)
identity=IdentityProgress.objects.select_related('current').get(listing_id=observation.listing_id)
assert identity.current.result['assistance']['review_id']==str(review.id)
queries=PostgresAssistanceQueries()
handler=AssistanceHandler(RequestReviewUseCase(repository),queries,ReadReviewsUseCase(queries))
client=Client(enforce_csrf_checks=True,HTTP_HOST="localhost")
with patch('garimpei.infra.http.assistance.routes.build_assistance_handler',return_value=handler):
 before=AssistanceReview.objects.count()
 response=client.get(f'/ofertas/{observation.listing_id}/ia/')
 assert response.status_code==200 and 'Evidências sustentadas'.encode() in response.content
 assert AssistanceReview.objects.count()==before
 assert client.post(f'/ofertas/{observation.listing_id}/ia/reavaliar/',{}).status_code==403
 token=client.cookies['csrftoken'].value
 form=dict(expected_revision=observation.ordinal,purpose='identity',command_id=str(uuid4()),csrfmiddlewaretoken=token)
 first=client.post(f'/ofertas/{observation.listing_id}/ia/reavaliar/',form)
 second=client.post(f'/ofertas/{observation.listing_id}/ia/reavaliar/',form)
 assert first.status_code==second.status_code==202
 assert client.put(f'/ofertas/{observation.listing_id}/ia/reavaliar/',{},HTTP_X_CSRFTOKEN=token).status_code==405
condition=repository.admit(ReviewCommand(uuid4(),'condition',observation.listing_id,observation.ordinal))
assert requested==['condition']
OperationalUnit.objects.create(id=uuid4(),installation='synthetic',stage='inference',key='PRIVATE_SENTINEL_COOKIE',revision=1,pending_since=now(),reason='PRIVATE_SENTINEL_COOKIE')
snapshot=capture_operations_snapshot()
assert 'PRIVATE_SENTINEL_COOKIE' not in json.dumps(snapshot.facts)
operation=repository.admit(ReviewCommand(uuid4(),'operations',snapshot.id,snapshot.revision))
assert AssistanceReview.objects.get(pk=operation.id).observation_id is None
assert ListingObservation.objects.count()>=1
original=len(AssistanceOperationsSnapshot.objects.all())
assert capture_operations_snapshot().id==snapshot.id
assert AssistanceOperationsSnapshot.objects.count()==original
"""


def test_assistance_idempotency_consumption_http_csrf_and_sanitized_operations(
    foundations: list[FoundationInstance],
) -> None:
    run_assert(foundations[0], SCRIPT)


RETENTION_SCRIPT = r"""
import json
from decimal import Decimal
from uuid import uuid4
from django.utils.timezone import now
from garimpei.domain.inference.ports import PreparedPart
from garimpei.domain.assistance.review import validate_assistance_output
from garimpei.domain.valuation.policy import estimate
from garimpei.infra.persistence.assistance_models import AssistancePolicy,AssistanceReview
from garimpei.infra.persistence.listing_models import ListingObservation
from garimpei.infra.persistence.identity_models import IdentityProgress
from tests.factories.assistance import seed_observation
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.repository.assistance.postgres_repository import PostgresAssistanceRepository
from garimpei.infra.repository.assistance.retention import reviewed_candidates
from garimpei.infra.gateway.assistance.snapshots import observation_snapshot
from garimpei.infra.repository.valuation.identity_repository import PostgresIdentityRepository
from garimpei.infra.repository.valuation.identity_mapper import current_identification
from garimpei.infra.repository.valuation.mapper import listing_comparable
from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase

class NamedFinitePreparer:
 def artifact(self): return 'controlled-pair-artifact'
 def prepare(self,value): return (PreparedPart('text',value.text,profile=value.prompt_version),)

rows=[]
for fixture in ('text','unicode','hostile','image-a','image-b','authorized-photo'):
 identity,_=seed_observation('f23-retention',fixture)
 observation=ListingObservation.objects.select_related('listing').get(pk=identity)
 observation.evidence=dict(observation.evidence,title='PlayStation 5 Slim Digital 825GB',description='Usado. Funcionando perfeitamente.',condition='Usado — seminovo',source_available=True)
 observation.price=Decimal('2000');observation.save(update_fields=['evidence','price'])
 PostgresIdentityRepository(now)._record(observation.listing_id)
 rows.append(observation.listing)
target=rows[0]
inference=PostgresInferenceRepository(lambda:0,100)
repository=PostgresAssistanceRepository(RequestAnalysisUseCase(inference,NamedFinitePreparer()))
for candidate in rows[1:]:
 snapshot=observation_snapshot(target,'comparables',candidate.latest)
 review=repository._create('comparables','listing_observation',target.latest.id,target.latest.ordinal,snapshot,target.latest,candidate.latest)
 work=inference.claim(now());assert work
 payload=dict(outcome='supported',findings=[dict(field=f['field'],value=f['value'],evidence_refs=[f['id']],reason_code='explicit_evidence') for f in snapshot['facts']],limitations=[])
 validated=validate_assistance_output('comparable-review-v1',json.dumps(payload),work.part.text)
 assert inference.publish(work,validated,{'controlled_fake':True},now())
 repository._complete(review)
 review.refresh_from_db();assert review.state=='supported'
AssistancePolicy.objects.update_or_create(pk=1,defaults=dict(active=True,adopted_at=now()))
comparable=listing_comparable(target,current_identification(target))
candidates=tuple(listing_comparable(row,current_identification(row)) for row in rows[1:])
retained,references=reviewed_candidates(comparable,candidates,uuid4())
assert len(retained)==len(references)==5
assert estimate(comparable,retained,now()).price==Decimal('2000')
progress=IdentityProgress.objects.get(listing=rows[1]);progress.manual_revision+=1;progress.save(update_fields=['manual_revision'])
retained,references=reviewed_candidates(comparable,candidates)
assert len(retained)==4 and estimate(comparable,retained,now()).reason=='amostra_insuficiente'
AssistancePolicy.objects.filter(pk=1).update(active=False)
"""


def test_f23_comparable_retention_preserves_f06_and_invalidates_manual_revision(
    foundations: list[FoundationInstance],
) -> None:
    run_assert(foundations[1], RETENTION_SCRIPT)
