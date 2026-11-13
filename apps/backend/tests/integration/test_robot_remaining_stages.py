from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE


def test_old_valuation_assessment_identity_and_research_work_obey_pause_without_spending_attempts(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, _, channel):
        group = pause_worker(instance)
        before_new_calls = source.new_calls
        before_posts = len([call for call in channel.calls if call[0] == "POST"])
        try:
            shell(
                instance,
                PREPARE
                + """
from uuid import uuid4
from django.utils.timezone import now as wall_clock
from garimpei.main import build_robot_repository,build_read_robot_status,build_valuation_handler,build_assessment_handler,build_identity_repository,build_read_monitoring_configuration
from garimpei.domain.robot.control import RobotCommand
from garimpei.infra.persistence.valuation_models import ValuationWork,ValuationProgress,ValuationEvaluation
from garimpei.infra.persistence.assessment_models import ConditionAssessment
from garimpei.infra.persistence.inference_models import InferenceRequest
from garimpei.infra.persistence.identity_models import IdentityProgress,ProductIdentification
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.research_models import ComparableInvestigation
from garimpei.infra.repository.valuation.research_repository import PostgresComparableResearchRepository
from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
from garimpei.usecase.valuation.run_research_usecase import RunComparableResearchUseCase
from tests.factories.comparable_research import NOW,KEY,controlled_limits,seed_case,ControlledResearchSource
robot=build_robot_repository();status=build_read_robot_status()
progress=ValuationProgress.objects.select_related('current__work').get(listing=l)
old=progress.current.work
progress.requested+=1;progress.save(update_fields=['requested'])
pending=ValuationWork.objects.create(listing=l,revision=progress.requested,snapshot=old.snapshot,requested_at=now,next_attempt_at=now,lease_until=now+timedelta(seconds=60),attempts=1)
# This target has no persisted automatic identification, so the identity reconciler really has pending input.
target=seed_case('22801')
assert not IdentityProgress.objects.filter(listing=target,current__isnull=False).exists()
publication=PostgresCollectionRepository(build_read_monitoring_configuration(),lambda:NOW,lambda *_:0,40)
research=PostgresComparableResearchRepository(build_read_monitoring_configuration(),lambda:NOW,controlled_limits(),publication)
research.reconcile()
row=ComparableInvestigation.objects.get(product_key=KEY,state='pending')
assert row.attempts==0 and row.pages==0
# Select this controlled target; other legitimate investigations belong to other cases.
ComparableInvestigation.objects.exclude(id=row.id).update(state='superseded',reason='controlled_other_case')
counts=(ValuationEvaluation.objects.count(),ConditionAssessment.objects.count(),InferenceRequest.objects.count(),ProductIdentification.objects.count())
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
build_valuation_handler().execute(pending.id)
build_assessment_handler().execute()
build_identity_repository().reconcile()
blocked_source=ControlledResearchSource()
RunComparableResearchUseCase(research,blocked_source,lambda:0.0,robot=robot,on_pause=research.pause_claim).execute()
row.refresh_from_db();pending.refresh_from_db()
assert row.attempts==0 and row.pages==0 and row.state=='pending' and row.lease_until is None
assert not blocked_source.calls
assert pending.attempts==0 and pending.lease_until is None and not pending.completed
assert counts==(ValuationEvaluation.objects.count(),ConditionAssessment.objects.count(),InferenceRequest.objects.count(),ProductIdentification.objects.count())
# A real persisted research page may finish after pause; the next detail cannot start.
class PausingResearchSource(ControlledResearchSource):
 def search(self, scope, query, continuation):
  value=super().search(scope,query,continuation)
  robot.command(RobotCommand(uuid4(),False,status.execute().revision))
  return value
robot.command(RobotCommand(uuid4(),True,status.execute().revision))
page_source=PausingResearchSource()
RunComparableResearchUseCase(research,page_source,lambda:0.0,robot=robot,on_pause=research.pause_claim).execute()
row.refresh_from_db()
assert page_source.calls==[('search',None)]
assert row.pages==1 and row.failures==0 and row.buffer and row.lease_until is None
assert row.state=='waiting_evidence' and row.reason=='robot_paused'
print('ROBOT_REMAINING_STAGES_PASS')
""",
            )
            assert source.new_calls == before_new_calls
            assert len([call for call in channel.calls if call[0] == "POST"]) == before_posts
        finally:
            resume_worker(group)
