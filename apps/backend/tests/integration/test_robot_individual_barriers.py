from pathlib import Path

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.listing import serve
from tests.factories.navigation import NavigationSourceFake, prepare_navigation_instance
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell
from tests.integration.test_first_alert_review_regressions import PREPARE
from tests.integration.test_navigation import BOOTSTRAP


@pytest.mark.parametrize("barrier", ["ia", "alerts", "recovery"])
def test_global_enable_conserves_individual_barrier_and_actual_stage_refuses(
    tmp_path: Path, barrier: str
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, _, channel):
        group = pause_worker(instance)
        before_new = source.new_calls
        try:
            shell(
                instance,
                PREPARE
                + f"\nbarrier={barrier!r}\n"
                + """
from uuid import uuid4
from garimpei.main import build_robot_repository,build_read_robot_status,build_integration_repository,build_alert_handler,build_valuation_handler
from garimpei.domain.robot.control import RobotCommand
from garimpei.domain.integration.values import Group
from garimpei.config.env import load_config
from garimpei.infra.persistence.operations_models import RecoveryBarrier
from garimpei.infra.persistence.integration_models import IntegrationSettings
from garimpei.infra.persistence.inference_models import InferenceControl,InferencePart
from garimpei.infra.persistence.valuation_models import ValuationWork,ValuationProgress
from garimpei.domain.inference.request import AnalysisInput
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.infra.persistence.management.commands.local_ai import _smoke_observation
from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase
robot=build_robot_repository();status=build_read_robot_status()
s.publish(l.id,s.prepare(l.id),build_read_profit().execute(l.id),now)
intent=FirstAlertIdentity.objects.get(listing=l).intent
assert intent is not None and intent.state=='queued'
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
if barrier=='ia':
 observation,text=_smoke_observation('robot-specific-pause','text')
 repo=PostgresInferenceRepository(lambda:0,3,robot=robot)
 ticket=repo.admit(AnalysisInput(observation,1,text,()),'fixture',(PreparedPart('one',text),))
 repo.control(True,InferenceControl.objects.get(pk=1).revision)
if barrier=='alerts':
 build_integration_repository().configure_whatsapp('synthetic','200@c.us',Group('100@g.us','Synthetic group'),False)
if barrier=='recovery':
 RecoveryBarrier.objects.create(installation=load_config().environment_id,backup_id=uuid4(),snapshot_at=now,restored_at=now,state='blocked')
robot.command(RobotCommand(uuid4(),True,status.execute().revision))
assert status.execute().enabled
if barrier=='ia':
 class NoInferenceAllowed:
  def infer(self,*args):raise AssertionError('IA pause was bypassed')
 assert RunAnalysisUseCase(repo,NoInferenceAllowed(),lambda:now).execute() is False
 assert InferenceControl.objects.get(pk=1).paused
 assert InferencePart.objects.get(request_id=ticket.request_id).attempts==0
 # Independent valid work can progress while the particular IA preference stays paused.
 progress=ValuationProgress.objects.select_related('current__work').get(listing=l)
 original=progress.current.work
 progress.requested+=1;progress.save(update_fields=['requested'])
 pending=ValuationWork.objects.create(listing=l,revision=progress.requested,snapshot=original.snapshot,requested_at=now,next_attempt_at=now,attempts=1,lease_until=now+timedelta(seconds=60))
 build_valuation_handler().execute(pending.id)
 pending.refresh_from_db();assert pending.completed
 assert InferenceControl.objects.get(pk=1).paused
elif barrier=='alerts':
 build_alert_handler('send').execute()
 assert not IntegrationSettings.objects.get(pk='local').alerts_enabled
 assert not intent.attempts.exists()
elif barrier=='recovery':
 assert build_alert_store().claim(intent.id,binding,now,reconcile=False) is None
 assert RecoveryBarrier.objects.get(installation=load_config().environment_id).state=='blocked'
 assert not intent.attempts.exists()
print('ROBOT_INDIVIDUAL_BARRIER_PASS:'+barrier)
""",
            )
            assert not [call for call in channel.calls if call[0] == "POST"]
            assert source.new_calls == before_new + (1 if barrier == "ia" else 0)
        finally:
            resume_worker(group)


def test_global_enable_does_not_clear_access_suspension_or_start_browser(tmp_path: Path) -> None:
    source = NavigationSourceFake()
    with serve(source) as origin:
        root = Path(__file__).resolve().parents[4]
        instance = prepare_navigation_instance(root, tmp_path, origin)
        started = instance.command("./scripts/init.sh", "--disposable")
        assert started.returncode == 0, started.stdout + started.stderr
        group = pause_worker(instance)
        try:
            shell(
                instance,
                BOOTSTRAP
                + """
from garimpei.main import build_robot_repository,build_read_robot_status,build_listing_task_handler
from garimpei.domain.robot.control import RobotCommand
robot=build_robot_repository();status=build_read_robot_status()
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
CollectionState.objects.filter(id=state.id).update(access_suspended=True)
robot.command(RobotCommand(uuid4(),True,status.execute().revision))
build_listing_task_handler().execute(str(attempt.cycle_id),attempt.generation)
state.refresh_from_db();assert state.access_suspended
assert not NavigationUnitReceipt.objects.exists()
print('ROBOT_ACCESS_BARRIER_PASS')
""",
            )
            assert not source.calls
        finally:
            resume_worker(group)
            stopped = instance.command("./scripts/stop.sh", "--clean")
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr
