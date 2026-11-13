from pathlib import Path

from tests.factories.media import generate_corpus, prepare_media_instance, serve_media
from tests.factories.runtime import pause_worker, resume_worker


def test_queued_media_waits_without_attempt_and_each_photo_is_separately_admitted(
    tmp_path: Path,
) -> None:
    generate_corpus()
    with serve_media() as (origin, requests):
        root = Path(__file__).resolve().parents[4]
        instance = prepare_media_instance(root, tmp_path, origin)
        started = instance.command("./scripts/init.sh", "--disposable")
        assert started.returncode == 0, started.stdout + started.stderr
        group = pause_worker(instance)
        try:
            result = instance.shell(
                """
from uuid import UUID,uuid4
from tests.factories.media import seed_media_cases
from garimpei.main import build_robot_repository,build_read_robot_status,build_media_runner
from garimpei.domain.robot.control import RobotCommand
from garimpei.infra.persistence.media_models import MediaJob,MediaAsset
"""
                + "rows=seed_media_cases("
                + repr(origin)
                + ")\n"
                + """
robot=build_robot_repository(); status=build_read_robot_status()
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
first=MediaJob.objects.filter(entry__capture__observation__listing_id=UUID(rows['A']['listing']),kind='download').order_by('id').first()
assert first and first.attempts==0
build_media_runner().execute(first.id)
first.refresh_from_db(); assert first.attempts==0 and first.state=='pending'
assert not MediaAsset.objects.exists()
robot.command(RobotCommand(uuid4(),True,status.execute().revision))
build_media_runner().execute(first.id)
first.refresh_from_db(); assert first.state=='done' and first.attempts==1
assert MediaAsset.objects.filter(state='available').count()==1
robot.command(RobotCommand(uuid4(),False,status.execute().revision))
next_job=MediaJob.objects.filter(kind='download').exclude(state='done').first()
assert next_job
build_media_runner().execute(next_job.id)
next_job.refresh_from_db(); assert next_job.attempts==0 and next_job.state=='pending'
assert MediaAsset.objects.filter(state='available').count()==1
assert not status.execute().enabled
print('ROBOT_MEDIA_PASS')
"""
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert len(requests) == 1
        finally:
            resume_worker(group)
            stopped = instance.command("./scripts/stop.sh", "--clean")
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr
