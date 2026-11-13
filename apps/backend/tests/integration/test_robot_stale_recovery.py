from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker
from tests.integration.test_robot_control import robot_instance as robot_instance


def test_enable_keeps_gpu_occupied_and_never_publishes_superseded_observation(
    robot_instance: FoundationInstance,
) -> None:
    group = pause_worker(robot_instance)
    try:
        result = robot_instance.shell("""
from uuid import uuid4
from django.utils.timezone import now
from garimpei.domain.robot.control import RobotCommand
from garimpei.domain.inference.request import AnalysisInput
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.persistence.management.commands.local_ai import _smoke_observation
from garimpei.infra.persistence.listing_models import ListingObservation,CollectionCycle
from garimpei.infra.persistence.inference_models import InferenceControl,InferenceRequest,InferencePart
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.queries.inference.postgres_queries import PostgresInferenceQueries
from tests.factories.robot import _fresh
robot,status=_fresh()
old_id,text=_smoke_observation('robot-stale-resource','text')
repo=PostgresInferenceRepository(lambda:0,5,robot=robot)
old=repo.admit(AnalysisInput(old_id,1,text,()),'fixture',(PreparedPart('one',text),))
active=repo.claim(now());assert active and repo.authorize(active)
robot.command(RobotCommand(uuid4(),False,status.status().revision))
previous=ListingObservation.objects.select_related('listing','cycle').get(pk=old_id)
new_cycle=CollectionCycle.objects.create(state=previous.cycle.state,scope_key=previous.cycle.scope_key,revision=2,phase='complete',started_at=now(),finished_at=now())
current=ListingObservation.objects.create(listing=previous.listing,cycle=new_cycle,ordinal=2,observed_at=now(),evidence=previous.evidence,coverage=previous.coverage)
listing=previous.listing;listing.latest=current;listing.ordinal=2;listing.save(update_fields=['latest','ordinal'])
new=repo.admit(AnalysisInput(current.id,2,text+' current',()),'fixture',(PreparedPart('new',text+' current'),))
robot.command(RobotCommand(uuid4(),True,status.status().revision))
assert repo.claim(now()) is None,'global enable ignored old occupied GPU generation'
assert InferenceControl.objects.get(pk=1).active_request==old.request_id
assert not repo.publish(active,{'findings':[],'unknowns':['old'],'limitations':[]},{},now())
assert InferenceRequest.objects.get(pk=old.request_id).state=='superseded'
listing.refresh_from_db();assert listing.latest_id==current.id
new_work=repo.claim(now());assert new_work and new_work.request_id==new.request_id
assert new_work.generation>active.generation and repo.authorize(new_work)
assert repo.publish(new_work,{'findings':[],'unknowns':['current'],'limitations':[]},{},now())
assert PostgresInferenceQueries().analysis(new.request_id)['state']=='succeeded'
assert repo.publish(active,{}, {},now()) is False
assert InferenceRequest.objects.get(pk=new.request_id).state=='succeeded'
assert not InferenceControl.objects.get(pk=1).active_request
print('ROBOT_STALE_RESOURCE_PASS')
""")
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        resume_worker(group)
