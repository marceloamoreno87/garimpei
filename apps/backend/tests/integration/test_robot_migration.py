from pathlib import Path
from uuid import uuid4

from garimpei.infra.runtime.processes import is_live, stop_process
from tests.factories.runtime import prepare_instance


def test_adoption_preserves_legacy_authorizations_and_individual_pause(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    instance = prepare_instance(root, tmp_path, "f22_adopt_" + uuid4().hex[:8])
    started = instance.command("./scripts/init.sh", "--disposable")
    assert started.returncode == 0, started.stdout + started.stderr
    try:
        owners = instance.manifest["processes"]
        for owner in owners:
            assert stop_process(owner, root, 10)
            assert not is_live(owner)
        result = instance.shell("""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils.timezone import now
from uuid import uuid4
executor=MigrationExecutor(connection)
legacy=[('runtime','0025_merge_identity_research')]
executor.migrate(legacy)
# Historical rows must use the schema actually installed, including after F21 adds fields.
apps=executor.loader.project_state(legacy).apps
AlertIntent=apps.get_model('runtime','AlertIntent')
AlertAttempt=apps.get_model('runtime','AlertAttempt')
InferenceControl=apps.get_model('runtime','InferenceControl')
InferenceControl.objects.get_or_create(pk=1)
InferenceControl.objects.filter(pk=1).update(paused=True,active_request=uuid4(),reason='execution_unknown')
intent=AlertIntent.objects.create(state='uncertain',session='synthetic',recipient='100@g.us',account='200@c.us',body='frozen legacy body',financial={'unchanged':'yes'},created_at=now(),next_action=now())
AlertAttempt.objects.create(intent=intent,ordinal=1,generation=1,authorized_at=now(),state='uncertain')
with connection.cursor() as cursor:
 cursor.execute('SELECT count(*) FROM procrastinate_jobs'); jobs=cursor.fetchone()[0]
old=(intent.id,intent.body,intent.financial,intent.attempts.count())
adopted=[('runtime','0026_robot_control')]
executor=MigrationExecutor(connection);executor.migrate(adopted)
apps=executor.loader.project_state(adopted).apps
RobotControl=apps.get_model('runtime','RobotControl')
RobotOperation=apps.get_model('runtime','RobotOperation')
InferenceControl=apps.get_model('runtime','InferenceControl')
AlertIntent=apps.get_model('runtime','AlertIntent')
from garimpei.infra.queries.robot.postgres_queries import PostgresRobotQueries
assert RobotControl.objects.get(pk='local').requested_enabled
assert not RobotOperation.objects.exists()
assert InferenceControl.objects.get(pk=1).paused
intent=AlertIntent.objects.get(pk=old[0]);assert (intent.id,intent.body,intent.financial,intent.attempts.count())==old
with connection.cursor() as cursor:
 cursor.execute('SELECT count(*) FROM procrastinate_jobs');assert cursor.fetchone()[0]==jobs
status=PostgresRobotQueries().status();assert status.unknown==2 and status.state=='unknown'
print('ROBOT_MIGRATION_PASS')
""")
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        stopped = instance.command("./scripts/stop.sh", "--clean")
        assert stopped.returncode == 0, stopped.stdout + stopped.stderr
