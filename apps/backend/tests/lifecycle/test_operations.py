import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from garimpei.infra.runtime.manifest import instance_lock
from garimpei.infra.runtime.processes import is_live, stop_process
from tests.factories.runtime import FoundationInstance


def test_stop_restart_preserves_receipts_pending_work_and_session_marker(
    foundations: list[FoundationInstance],
) -> None:
    instance, other = foundations
    config = instance.config
    before = instance.manifest
    completed = instance.command(
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
    assert completed.returncode == 0, completed.stdout + completed.stderr
    with instance.database() as connection:
        completed_probe = connection.execute(
            "SELECT id FROM runtime_runtimeprobe WHERE environment_id=%s AND run_id=%s AND kind='manual' AND completed_at IS NOT NULL ORDER BY sequence DESC LIMIT 1",
            [config.environment_id, before["run_id"]],
        ).fetchone()
        assert completed_probe is not None
    waha = f"garimpei-{config.environment_id}-waha-1"
    marker = instance.command(
        "docker",
        "exec",
        waha,
        "sh",
        "-c",
        "printf foundation-marker > /app/.sessions/garimpei-synthetic-marker",
    )
    assert marker.returncode == 0
    expected = instance.command(
        "docker", "exec", waha, "sha256sum", "/app/.sessions/garimpei-synthetic-marker"
    ).stdout
    assert stop_process(before["processes"][1], instance.root, 10)
    queued = instance.shell(
        "from garimpei.infra.worker.probe_service import enqueue_manual; from garimpei.config.env import load_config; p=enqueue_manual(load_config()); print('PENDING:'+str(p.id))"
    )
    assert queued.returncode == 0, queued.stdout + queued.stderr
    pending = queued.stdout.split("PENDING:")[-1].strip()
    assert instance.command("./scripts/stop.sh").returncode == 0
    assert all(not is_live(record) for record in before["processes"])
    assert instance.command("./scripts/stop.sh").returncode == 0
    assert other.http("/health/ready")[0] == 200
    started = instance.command("./scripts/init.sh", "--disposable")
    assert started.returncode == 0, started.stdout + started.stderr
    assert instance.manifest["run_id"] != before["run_id"]
    assert (
        expected
        == instance.command(
            "docker", "exec", waha, "sha256sum", "/app/.sessions/garimpei-synthetic-marker"
        ).stdout
    )
    with instance.database() as connection:
        assert connection.execute(
            "SELECT completed_at IS NOT NULL FROM runtime_runtimeprobe WHERE id=%s",
            [completed_probe[0]],
        ).fetchone() == (True,)
        assert connection.execute(
            "SELECT completed_at IS NOT NULL FROM runtime_runtimeprobe WHERE id=%s", [pending]
        ).fetchone() == (True,)
        assert connection.execute(
            "SELECT count(*) > 0 FROM runtime_runtimeprobe WHERE run_id=%s AND completed_at IS NOT NULL",
            [before["run_id"]],
        ).fetchone() == (True,)


def test_worker_dead_or_stale_is_not_ready(foundations: list[FoundationInstance]) -> None:
    instance = foundations[0]
    assert stop_process(instance.manifest["processes"][1], instance.root, 10)
    time.sleep(15.1)
    status, _, body = instance.http("/health/ready")
    assert status == 503
    assert json.loads(body)["checks"]["worker"] == "unavailable"
    assert instance.http("/health")[0] == 200
    assert instance.command("./scripts/stop.sh").returncode == 0
    result = instance.command("./scripts/init.sh", "--disposable")
    assert result.returncode == 0, result.stdout + result.stderr


def test_active_instance_lock_refuses_concurrent_init(
    foundations: list[FoundationInstance],
) -> None:
    instance = foundations[0]
    with instance_lock(instance.config.directory):
        result = instance.command("./scripts/init.sh")
        assert result.returncode == 1
        assert "lock" in result.stderr.lower()


def test_foreign_pid_is_not_signalled(
    foundations: list[FoundationInstance], tmp_path: Path
) -> None:
    instance = foundations[0]
    path = instance.config.directory / "manifest.json"
    original = path.read_text()
    foreign = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"], cwd=tmp_path, start_new_session=True
    )
    try:
        manifest = json.loads(original)
        manifest["processes"][0]["pid"] = foreign.pid
        path.write_text(json.dumps(manifest))
        result = instance.command("./scripts/stop.sh")
        assert result.returncode != 0
        assert foreign.poll() is None
    finally:
        path.write_text(original)
        foreign.terminate()
        foreign.wait(timeout=5)
    assert instance.http("/health/ready")[0] == 200


@pytest.mark.parametrize(
    "field,value",
    [
        ("disposable", False),
        ("session_kind", "real"),
        ("session_kind", "unknown"),
        ("checkout", "/foreign-checkout"),
    ],
)
def test_clean_denies_unmarked_or_real_session(
    foundations: list[FoundationInstance], field: str, value: object
) -> None:
    instance = foundations[0]
    path = instance.config.directory / "manifest.json"
    original = path.read_text()
    try:
        manifest = json.loads(original)
        manifest[field] = value
        path.write_text(json.dumps(manifest))
        result = instance.command("./scripts/stop.sh", "--clean")
        assert result.returncode == 64
        assert "Cleaned" not in result.stdout
    finally:
        path.write_text(original)
    assert instance.http("/health/ready")[0] == 200


def test_clean_refuses_unknown_files_even_with_disposable_marker(
    foundations: list[FoundationInstance], tmp_path: Path
) -> None:
    instance = foundations[0]
    waha = f"garimpei-{instance.config.environment_id}-waha-1"
    assert (
        instance.command(
            "docker",
            "exec",
            waha,
            "sh",
            "-c",
            "printf synthetic-unknown > /app/.sessions/unknown-session-data",
        ).returncode
        == 0
    )
    result = instance.command("./scripts/stop.sh", "--clean")
    assert result.returncode == 64
    preserved = tmp_path / "preserved"
    assert (
        instance.command(
            "docker", "cp", waha + ":/app/.sessions/unknown-session-data", str(preserved)
        ).returncode
        == 0
    )
    assert preserved.read_text() == "synthetic-unknown"
    assert instance.command("docker", "start", waha).returncode == 0
    assert (
        instance.command(
            "docker", "exec", waha, "rm", "/app/.sessions/unknown-session-data"
        ).returncode
        == 0
    )
    result = instance.command("./scripts/init.sh", "--disposable")
    assert result.returncode == 0, result.stdout + result.stderr


def test_clean_in_dev_is_denied_before_removal(tmp_path: Path) -> None:
    from tests.factories.runtime import prepare_instance

    instance = prepare_instance(Path(__file__).resolve().parents[4], tmp_path, "dev_clean_case")
    with instance.private_file.open("a") as file:
        file.write("GARIMPEI_ENV=dev\n")
    result = instance.command("./scripts/stop.sh", "--clean")
    assert result.returncode == 64
    assert "Cleaned" not in result.stdout


def test_migrations_check_apply_and_invalid_arguments(
    foundations: list[FoundationInstance],
) -> None:
    instance = foundations[0]
    for argument in ["--check", "--apply", "--apply", "--check"]:
        result = instance.command("./scripts/migrate-dev.sh", argument)
        assert result.returncode == 0, result.stdout + result.stderr
    assert instance.command("./scripts/migrate-dev.sh", "--not-a-mode").returncode == 64
    assert instance.command("./scripts/migrate-dev.sh", "--make", "123invalid").returncode == 64


def test_explicit_occupied_port_preserves_owner(tmp_path: Path) -> None:
    from tests.factories.runtime import prepare_instance

    root = Path(__file__).resolve().parents[4]
    instance = prepare_instance(root, tmp_path, "occupied_" + tmp_path.name.replace("-", "_")[-12:])
    with socket.socket() as owner:
        owner.bind(("127.0.0.1", 0))
        owner.listen()
        with instance.private_file.open("a") as file:
            file.write(f"GARIMPEI_WEB_PORT={owner.getsockname()[1]}\n")
        result = instance.command("./scripts/init.sh", "--disposable")
        assert result.returncode == 1
        assert "Port" in result.stderr
        assert owner.fileno() >= 0
        assert "Ready" not in result.stdout


@pytest.mark.parametrize(
    "key,value",
    [
        (str(case["key"]), str(case["value"]))
        for case in json.loads(
            (Path(__file__).resolve().parents[1] / "fixtures/foundation/cases.json").read_text()
        )["configuration"]
    ],
)
def test_invalid_configuration_is_safe_precondition_failure(
    tmp_path: Path, key: str, value: str
) -> None:
    from tests.factories.runtime import prepare_instance

    instance = prepare_instance(Path(__file__).resolve().parents[4], tmp_path, "invalid_case")
    with instance.private_file.open("a") as file:
        file.write(key + "=" + value + "\n")
    result = instance.command("./scripts/init.sh")
    assert result.returncode == 64
    assert key in result.stderr
    assert "private-canary" not in result.stdout + result.stderr
    assert "Ready" not in result.stdout
