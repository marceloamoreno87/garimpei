"""Typed operations and candidate pairs use real PostgreSQL without fabricated listings."""

from tests.factories.runtime import FoundationInstance
from tests.integration.test_inference import run_assert


def test_operations_target_publication_and_database_legacy_guard(
    foundations: list[FoundationInstance],
) -> None:
    run_assert(
        foundations[0],
        """
from uuid import uuid4
from django.db import transaction, IntegrityError
from django.db.models import Max
from django.utils.timezone import now
from garimpei.domain.inference.request import AnalysisInput
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.persistence.assistance_models import AssistanceOperationsSnapshot
from garimpei.infra.persistence.inference_models import InferenceRequest
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
revision=(AssistanceOperationsSnapshot.objects.aggregate(value=Max('revision'))['value'] or 0)+1
snapshot=AssistanceOperationsSnapshot.objects.create(revision=revision,content_hash=uuid4().hex*2,facts={})
profile='operations-support-v1'
value=AnalysisInput(None,revision,'{"facts":[],"allowed_values":{}}',(),profile,profile,
 target_kind='operations_snapshot',target_id=snapshot.id,target_revision=revision)
repo=PostgresInferenceRepository(lambda:0,100)
part=PreparedPart('text',value.text,profile=profile)
ticket=repo.admit(value,'controlled-artifact',(part,))
assert InferenceRequest.objects.get(pk=ticket.request_id).observation_id is None
assert repo.admit(value,'controlled-artifact',(part,)).reused
work=repo.claim(now())
assert work and work.request_id==ticket.request_id
AssistanceOperationsSnapshot.objects.create(revision=revision+1,content_hash=uuid4().hex*2,facts={})
assert not repo.publish(work,{'outcome':'insufficient','findings':[],'limitations':[]},{},now())
assert PostgresInferenceQueries().analysis(ticket.request_id)['state']=='superseded'
try:
 repo.admit(value,'other-artifact',(part,))
 raise AssertionError('stale snapshot admitted')
except InferenceError as error:
 assert error.code=='target_revision_mismatch'
try:
 with transaction.atomic():
  InferenceRequest.objects.create(observation=None,revision=1,signature=uuid4().hex*2,
   artifact='controlled',prompt_version='local-evidence-v1',schema_version='local-evidence-v1',created_at=now())
 raise AssertionError('legacy NULL observation accepted by database')
except IntegrityError:
 pass
""",
    )


def test_different_comparable_pairs_do_not_supersede_each_other(
    foundations: list[FoundationInstance],
) -> None:
    run_assert(
        foundations[0],
        """
from uuid import uuid4
from django.utils.timezone import now
from garimpei.domain.inference.request import AnalysisInput
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
from garimpei.infra.persistence.management.commands.local_ai import _smoke_observation
identity,text=_smoke_observation('typed-pairs','text')
profile='comparable-review-v1'
repo=PostgresInferenceRepository(lambda:0,100)
base=dict(observation_id=identity,revision=1,text='{"facts":[],"allowed_values":{}}',images=(),
 prompt_version=profile,schema_version=profile,target_kind='listing_observation',target_id=identity,target_revision=1)
a=AnalysisInput(**base,context={'candidate_id':str(uuid4())})
b=AnalysisInput(**base,context={'candidate_id':str(uuid4())})
part=PreparedPart('text',a.text,profile=profile)
first=repo.admit(a,'pair-artifact',(part,))
second=repo.admit(b,'pair-artifact',(part,))
assert first.request_id!=second.request_id
assert PostgresInferenceQueries().analysis(first.request_id)['state']=='pending'
assert PostgresInferenceQueries().analysis(second.request_id)['state']=='pending'
""",
    )
