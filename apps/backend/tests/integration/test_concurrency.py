import sys
import time
import uuid

from garimpei.config.env import process_environment
from garimpei.infra.runtime.processes import start_process, stop_process
from tests.factories.runtime import FoundationInstance


def test_duplicate_control_with_two_consumers_has_one_successor(
    foundations: list[FoundationInstance],
) -> None:
    instance = foundations[0]
    manifest = instance.manifest
    assert stop_process(manifest["processes"][1], instance.root, 10)
    result = instance.shell("""
from django.db import transaction
from garimpei.infra.persistence.models import RuntimeProbe
from garimpei.config.env import load_config
from garimpei.main import defer_runtime_probe
c=load_config()
with transaction.atomic():
 p=RuntimeProbe.objects.filter(environment_id=c.environment_id,kind='control',completed_at__isnull=True,run_id=c.run_id).order_by('-sequence').first()
 assert p is not None
 defer_runtime_probe(str(p.id))
 defer_runtime_probe(str(p.id))
 print('TARGET:'+str(p.sequence))
""")
    assert result.returncode == 0, result.stdout + result.stderr
    sequence = int(result.stdout.split("TARGET:")[-1].strip())
    config = instance.config
    command = [sys.executable, str(instance.root / "apps/backend/manage.py"), "runworker"]
    records = [
        start_process(
            command,
            instance.root / "apps/backend",
            process_environment(config, manifest["run_id"]),
            config.directory / f"duplicate-{index}.log",
        )
        for index in range(2)
    ]
    try:
        deadline = time.monotonic() + 15
        with instance.database() as connection:
            while time.monotonic() < deadline:
                row = connection.execute(
                    "SELECT count(*) FROM runtime_runtimeprobe WHERE environment_id=%s AND run_id=%s AND kind='control' AND sequence=%s",
                    [config.environment_id, manifest["run_id"], sequence + 1],
                ).fetchone()
                if row == (1,):
                    break
                time.sleep(0.1)
            assert row == (1,)
            assert connection.execute(
                "SELECT count(*) FROM procrastinate_jobs j JOIN runtime_runtimeprobe p ON j.args->>'probe_id'=p.id::text WHERE p.environment_id=%s AND p.run_id=%s AND p.kind='control' AND p.sequence=%s",
                [config.environment_id, manifest["run_id"], sequence + 1],
            ).fetchone() == (1,)
    finally:
        for record in records:
            assert stop_process(record, instance.root, 10)
        assert instance.command("./scripts/stop.sh").returncode == 0
        result = instance.command("./scripts/init.sh", "--disposable")
        assert result.returncode == 0, result.stdout + result.stderr


def test_old_run_cannot_renew_current_readiness(foundations: list[FoundationInstance]) -> None:
    instance = foundations[0]
    assert stop_process(instance.manifest["processes"][1], instance.root, 10)
    old_run = str(uuid.uuid4())
    result = instance.shell(f"""
from django.db import connection,transaction
from garimpei.config.env import load_config
from garimpei.infra.persistence.models import RuntimeProbe
from garimpei.main import build_enqueue_app
c=load_config()
with transaction.atomic():
 p=RuntimeProbe.objects.create(environment_id=c.environment_id,run_id='{old_run}',kind='control',sequence=0)
 build_enqueue_app().configure_task(name='garimpei.runtime_probe',queue='old_control',connection=connection.connection).defer(probe_id=str(p.id))
print('OLD:'+str(p.id))
""")
    assert result.returncode == 0, result.stdout + result.stderr
    probe_id = result.stdout.split("OLD:")[-1].strip()
    config = instance.config
    with instance.database() as connection:
        before = connection.execute(
            "SELECT run_id,last_probe_at,probe_sequence FROM runtime_runtimestate WHERE environment_id=%s",
            [config.environment_id],
        ).fetchone()
    code = "from garimpei.main import register_tasks; register_tasks(); from django.core.management import call_command; call_command('procrastinate','worker','--queues','old_control')"
    command = [sys.executable, str(instance.root / "apps/backend/manage.py"), "shell", "-c", code]
    record = start_process(
        command,
        instance.root / "apps/backend",
        process_environment(config, instance.manifest["run_id"]),
        config.directory / "old-control.log",
    )
    try:
        deadline = time.monotonic() + 15
        with instance.database() as connection:
            row = None
            while time.monotonic() < deadline:
                row = connection.execute(
                    "SELECT completed_at IS NOT NULL FROM runtime_runtimeprobe WHERE id=%s",
                    [probe_id],
                ).fetchone()
                if row == (True,):
                    break
                time.sleep(0.1)
            assert row == (True,)
            assert (
                connection.execute(
                    "SELECT run_id,last_probe_at,probe_sequence FROM runtime_runtimestate WHERE environment_id=%s",
                    [config.environment_id],
                ).fetchone()
                == before
            )
            assert connection.execute(
                "SELECT count(*) FROM runtime_runtimeprobe WHERE run_id=%s AND sequence>0",
                [old_run],
            ).fetchone() == (0,)
    finally:
        assert stop_process(record, instance.root, 10)
        assert instance.command("./scripts/stop.sh").returncode == 0
        result = instance.command("./scripts/init.sh", "--disposable")
        assert result.returncode == 0, result.stdout + result.stderr
