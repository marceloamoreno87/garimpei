from pathlib import Path

from tests.factories.listing import serve
from tests.factories.navigation import NavigationSourceFake, prepare_navigation_instance
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_navigation import BOOTSTRAP, shell


def test_paused_navigation_preserves_checkpoint_lease_and_does_not_spin_continuations(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[4]
    with serve(NavigationSourceFake()) as url:
        instance = prepare_navigation_instance(root, tmp_path, url)
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
from garimpei.infra.repository.robot.ownership import process_reference
from garimpei.infra.persistence.robot_models import RobotOperation
robot=build_robot_repository();status=build_read_robot_status()
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
with connection.cursor() as cursor:
 cursor.execute('SELECT count(*) FROM procrastinate_jobs');before_jobs=cursor.fetchone()[0]
state.refresh_from_db();before=(state.lease_until,state.next_attempt_at,state.failures)
head=list(NavigationCheckpoint.objects.values('work_id','pages','details','cursor','pending_unit'))
for _ in range(4):
 build_listing_task_handler().execute(str(attempt.cycle_id),attempt.generation)
 nav.yield_slice(attempt,scope)
 reconcile_navigation()
with connection.cursor() as cursor:
 cursor.execute('SELECT count(*) FROM procrastinate_jobs');assert cursor.fetchone()[0]==before_jobs
state.refresh_from_db();assert before==(state.lease_until,state.next_attempt_at,state.failures)
assert head==list(NavigationCheckpoint.objects.values('work_id','pages','details','cursor','pending_unit'))
assert not NavigationUnitReceipt.objects.exists()
assert not RobotOperation.objects.exists()
# Unknown old permit remains unknown after worker ownership is lost, never completed from missing heartbeat.
robot.command(RobotCommand(uuid4(),True,status.execute().revision))
permit=robot.authorize('navigation','old-unit','revision:2',5);assert permit
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
assert status.execute().state=='draining'
RobotOperation.objects.filter(id=permit.id).update(worker_reference='999999999:0.0')
assert status.execute().state=='unknown'
assert RobotOperation.objects.get(id=permit.id).state=='active'
robot.complete(permit, 'completed','stage_recovery_proof')
assert status.execute().state=='disabled'
print('ROBOT_NAVIGATION_QUEUE_PASS')
""",
            )
        finally:
            resume_worker(group)
            stopped = instance.command("./scripts/stop.sh", "--clean")
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr
