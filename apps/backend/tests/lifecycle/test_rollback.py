import json
import os
import shutil
import socket
import sys
import uuid
from pathlib import Path

from garimpei.infra.runtime.processes import is_live, start_process
from tests.factories.runtime import prepare_instance


def test_shutdown_timeout_never_claims_completion(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    instance = prepare_instance(root, tmp_path, "timeout_" + uuid.uuid4().hex[:10])
    with instance.private_file.open("a") as file:
        file.write("GARIMPEI_SHUTDOWN_TIMEOUT_SECONDS=1\n")
    record = start_process(
        [
            sys.executable,
            "-c",
            "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('started',flush=True); time.sleep(60)",
        ],
        root / "apps/backend",
        dict(os.environ),
        tmp_path / "controlled.log",
    )
    import time

    deadline = time.monotonic() + 5
    while (
        "started" not in (tmp_path / "controlled.log").read_text() and time.monotonic() < deadline
    ):
        time.sleep(0.02)
    config = instance.config
    config.directory.mkdir(parents=True)
    metadata = {
        "environment_id": config.environment_id,
        "checkout": str(root),
        "run_id": str(uuid.uuid4()),
        "ports": {"web": config.web_port, "pg": config.pg_port, "waha": config.waha_port},
        "processes": [record],
        "containers": [],
        "disposable": True,
        "session_kind": "synthetic",
        "status": "ready",
    }
    (config.directory / "manifest.json").write_text(json.dumps(metadata))
    result = instance.command("./scripts/stop.sh")
    assert result.returncode == 1
    assert "completion is unknown" in result.stderr
    assert "completed" not in result.stdout
    assert not is_live(record)
    shutil.rmtree(config.directory)


def test_partial_start_preserves_volumes_and_existing_containers(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    instance = prepare_instance(root, tmp_path, "partial_" + uuid.uuid4().hex[:10])
    assert instance.command("./scripts/init.sh", "--disposable").returncode == 0
    config = instance.config
    assert instance.command("./scripts/stop.sh").returncode == 0
    postgres = f"garimpei-{config.environment_id}-postgres-1"
    assert instance.command("docker", "start", postgres).returncode == 0
    with instance.database() as connection:
        connection.execute("CREATE TABLE preservation_marker(value text)")
        connection.execute("INSERT INTO preservation_marker VALUES ('keep')")
    foreign = socket.socket()
    foreign.bind(("127.0.0.1", 0))
    foreign.listen()
    # Recreate only this stopped WAHA with a deliberately unavailable host port.
    manifest = instance.manifest
    waha = f"garimpei-{config.environment_id}-waha-1"
    assert instance.command("docker", "rm", waha).returncode == 0
    manifest["containers"] = [
        identifier
        for identifier in manifest["containers"]
        if instance.command("docker", "inspect", identifier).returncode == 0
    ]
    manifest["ports"]["waha"] = foreign.getsockname()[1]
    (config.directory / "manifest.json").write_text(json.dumps(manifest))
    with instance.private_file.open("a") as file:
        file.write(f"GARIMPEI_WAHA_PORT={foreign.getsockname()[1]}\n")
    try:
        result = instance.command("./scripts/init.sh", "--disposable")
        assert result.returncode == 1
        assert "Ready" not in result.stdout
        with instance.database() as connection:
            assert connection.execute("SELECT value FROM preservation_marker").fetchone() == (
                "keep",
            )
        running = instance.command("docker", "inspect", "--format", "{{.State.Running}}", postgres)
        assert running.stdout.strip() == "true"
        assert foreign.fileno() >= 0
    finally:
        foreign.close()
        assert instance.command("./scripts/stop.sh", "--clean").returncode == 0
