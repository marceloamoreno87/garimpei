import json
import time
import uuid

import pytest

from tests.factories.runtime import FoundationInstance


def test_manual_probe_runs_while_web_is_stopped(foundations: list[FoundationInstance]) -> None:
    from garimpei.infra.runtime.processes import stop_process

    instance = foundations[0]
    assert stop_process(instance.manifest["processes"][0], instance.root, 10)
    result = instance.command(
        "uv",
        "run",
        "--project",
        "apps/backend",
        "--frozen",
        "--no-sync",
        "python",
        "apps/backend/manage.py",
        "runtime_probe",
        "--wait",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "completed" in result.stdout
    assert instance.command("./scripts/stop.sh").returncode == 0
    result = instance.command("./scripts/init.sh", "--disposable")
    assert result.returncode == 0, result.stdout + result.stderr


def test_two_instances_have_distinct_resources_and_local_binds(
    foundations: list[FoundationInstance],
) -> None:
    first, second = foundations
    assert first.config.environment_id != second.config.environment_id
    assert first.config.database != second.config.database
    assert {first.config.web_port, first.config.pg_port, first.config.waha_port}.isdisjoint(
        {second.config.web_port, second.config.pg_port, second.config.waha_port}
    )
    for instance in foundations:
        status, _, body = instance.http("/health/ready")
        assert status == 200
        assert json.loads(body)["checks"] == dict.fromkeys(
            ["database", "migrations", "worker", "waha"], "ready"
        )
        bindings = instance.command(
            "docker",
            "ps",
            "--filter",
            "label=com.garimpei.environment=" + instance.config.environment_id,
            "--format",
            "{{.Ports}}",
        )
        assert "0.0.0.0:" not in bindings.stdout
        assert bindings.stdout.count("127.0.0.1:") == 2


def test_init_is_idempotent_and_runtime_probe_is_real(
    foundations: list[FoundationInstance],
) -> None:
    instance = foundations[0]
    before = instance.manifest
    result = instance.command("./scripts/init.sh", "--disposable")
    assert result.returncode == 0, result.stdout + result.stderr
    assert instance.manifest == before
    result = instance.command(
        "uv",
        "run",
        "--project",
        "apps/backend",
        "--frozen",
        "--no-sync",
        "python",
        "apps/backend/manage.py",
        "runtime_probe",
        "--wait",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "completed" in result.stdout


@pytest.mark.parametrize(
    "method,host,expected", [("GET", "not-allowed.example", 400), ("OPTIONS", "127.0.0.1", 405)]
)
def test_real_http_boundaries(
    foundations: list[FoundationInstance], method: str, host: str, expected: int
) -> None:
    assert foundations[0].http("/health/ready", method=method, host=host)[0] == expected


@pytest.mark.parametrize("service", ["postgres", "waha"])
def test_dependency_failure_is_not_liveness_failure(
    foundations: list[FoundationInstance], service: str
) -> None:
    instance = foundations[0]
    name = f"garimpei-{instance.config.environment_id}-{service}-1"
    assert instance.command("docker", "stop", name).returncode == 0
    try:
        started = time.monotonic()
        status, _, body = instance.http("/health/ready")
        assert status == 503 and time.monotonic() - started <= 10
        data = json.loads(body)
        assert data["checks"]["database" if service == "postgres" else "waha"] == "unavailable"
        assert data["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
        if service == "postgres":
            assert data["checks"]["migrations"] == data["checks"]["worker"] == "unavailable"
        secrets = dict(
            line.split("=", 1) for line in instance.private_file.read_text().splitlines()
        )
        assert all(
            secrets[key] not in body
            for key in ("DJANGO_SECRET_KEY", "POSTGRES_PASSWORD", "WAHA_API_KEY")
        )
        assert instance.http("/health")[0] == 200
    finally:
        assert instance.command("docker", "start", name).returncode == 0
        time.sleep(2)


def test_commit_and_rollback_share_real_postgres_transaction(
    foundations: list[FoundationInstance],
) -> None:
    instance = foundations[0]
    token = str(uuid.uuid4())
    code = f"""
import psycopg,time
from django.db import transaction,connection
from garimpei.infra.worker.probe_service import enqueue_manual
from garimpei.config.env import load_config
c=load_config()
observer=psycopg.connect(c.database_url,autocommit=True)
with transaction.atomic():
 p=enqueue_manual(c)
 assert observer.execute('select count(*) from runtime_runtimeprobe where id=%s',[p.id]).fetchone()[0]==0
 assert observer.execute("select count(*) from procrastinate_jobs where args->>'probe_id'=%s",[str(p.id)]).fetchone()[0]==0
committed=p.id
assert observer.execute('select count(*) from runtime_runtimeprobe where id=%s',[committed]).fetchone()[0]==1
assert observer.execute("select count(*) from procrastinate_jobs where args->>'probe_id'=%s",[str(committed)]).fetchone()[0]==1
try:
 with transaction.atomic():
  p=enqueue_manual(c)
  raise ValueError('{token}')
except ValueError: pass
assert observer.execute('select count(*) from runtime_runtimeprobe where id=%s',[p.id]).fetchone()[0]==0
assert observer.execute("select count(*) from procrastinate_jobs where args->>'probe_id'=%s",[str(p.id)]).fetchone()[0]==0
time.sleep(15)
assert observer.execute('select count(*) from runtime_runtimeprobe where id=%s',[p.id]).fetchone()[0]==0
assert observer.execute("select count(*) from procrastinate_jobs where args->>'probe_id'=%s",[str(p.id)]).fetchone()[0]==0
assert observer.execute('select completed_at is not null from runtime_runtimeprobe where id=%s',[committed]).fetchone()[0]
print('ATOMIC_COMMIT_ROLLBACK_OK')
"""
    result = instance.shell(code)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ATOMIC_COMMIT_ROLLBACK_OK" in result.stdout


def test_pending_migration_degrades_readiness_without_applying(
    foundations: list[FoundationInstance],
) -> None:
    instance = foundations[0]
    with instance.database() as connection:
        row = connection.execute(
            "DELETE FROM django_migrations WHERE id = ("
            "SELECT id FROM django_migrations WHERE app='runtime' ORDER BY id DESC LIMIT 1"
            ") RETURNING name, applied"
        ).fetchone()
        assert row is not None
        try:
            status, _, body = instance.http("/health/ready")
            assert status == 503
            assert json.loads(body)["checks"]["migrations"] == "unavailable"
            assert instance.command("./scripts/migrate-dev.sh", "--check").returncode == 1
            assert connection.execute(
                "SELECT count(*) FROM django_migrations WHERE app='runtime' AND name=%s", [row[0]]
            ).fetchone() == (0,)
        finally:
            connection.execute(
                "INSERT INTO django_migrations(app,name,applied) VALUES ('runtime',%s,%s)",
                row,
            )
    assert instance.command("./scripts/migrate-dev.sh", "--check").returncode == 0
