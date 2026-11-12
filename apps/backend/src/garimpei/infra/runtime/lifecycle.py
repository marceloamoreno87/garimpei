from __future__ import annotations

import json
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import replace
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import django
from django.core.management import call_command
from django.db import DatabaseError, connection

from garimpei.config.env import (
    ConfigurationError,
    RuntimeConfig,
    activate_environment,
    process_environment,
)
from garimpei.infra.runtime.containers import (
    compose,
    container_ids,
    docker,
    network_ids,
    running_containers,
    stop_containers,
    verify_container,
    verify_network,
)
from garimpei.infra.runtime.manifest import (
    Manifest,
    OperationError,
    instance_lock,
    read_manifest,
    write_manifest,
)
from garimpei.infra.runtime.processes import is_live, start_process, stop_process, verify_process


def _setup(config: RuntimeConfig, run_id: str) -> RuntimeConfig:
    active = replace(config, run_id=run_id)
    activate_environment(active, run_id)
    django.setup()
    return active


def _check_port(port: int) -> None:
    try:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", port))
    except OSError:
        raise OperationError(f"Port {port}: unavailable; expected unused loopback port") from None


def _assert_manifest(manifest: Manifest, config: RuntimeConfig) -> None:
    if manifest["environment_id"] != config.environment_id or manifest["checkout"] != str(
        config.root
    ):
        raise OperationError("Manifest ownership: environment/checkout mismatch")
    for process in manifest["processes"]:
        verify_process(process, config.root)
    for identifier in manifest["containers"]:
        verify_container(identifier, config)
    for identifier in network_ids(config):
        verify_network(identifier, config, manifest["containers"])


def _ready(config: RuntimeConfig, run_id: str) -> bool:
    try:
        with urlopen(f"http://127.0.0.1:{config.web_port}/health/ready", timeout=3) as response:
            body = json.load(response)
            return bool(
                response.status == 200
                and body.get("environment_id") == config.environment_id
                and body.get("run_id") == run_id
            )
    except (URLError, OSError, ValueError):
        return False


def _wait_database(config: RuntimeConfig, deadline: float) -> None:
    from garimpei.main import build_database_probe

    probe = build_database_probe()
    while time.monotonic() < deadline:
        if probe.check():
            return
        time.sleep(0.2)
    raise OperationError("PostgreSQL: authenticated readiness timeout")


def _spawn(config: RuntimeConfig, manifest: Manifest) -> None:
    backend = config.root / "apps/backend"
    environment = process_environment(config, config.run_id)
    logging_config = config.directory / "logging.json"
    logging_config.write_text(
        json.dumps(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "loggers": {
                    "gunicorn.error": {
                        "handlers": ["console"],
                        "level": "INFO",
                        "propagate": False,
                    },
                    "gunicorn.access": {
                        "handlers": ["console"],
                        "level": "INFO",
                        "propagate": False,
                    },
                },
                "formatters": {"json": {"()": "garimpei.infra.runtime.logging.JsonFormatter"}},
                "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
                "root": {"handlers": ["console"], "level": config.log_level},
            }
        )
    )
    commands = [
        [
            sys.executable,
            "-m",
            "gunicorn",
            "garimpei.config.wsgi:application",
            "--bind",
            f"127.0.0.1:{config.web_port}",
            "--workers",
            "1",
            "--log-config-json",
            str(logging_config),
        ],
        [sys.executable, str(backend / "manage.py"), "runworker"],
    ]
    for name, command in zip(("web", "worker"), commands, strict=True):
        manifest["processes"].append(
            start_process(command, backend, environment, config.directory / f"{name}.log")
        )
        write_manifest(config.directory, manifest)


def start(config: RuntimeConfig, *, disposable: bool = False) -> None:
    if shutil.which("docker") is None:
        raise ConfigurationError("docker: expected Docker with Compose")
    with instance_lock(config.directory):
        previous = read_manifest(config.directory)
        if previous is not None:
            _assert_manifest(previous, config)
        active = previous and any(is_live(process) for process in previous["processes"])
        if active and previous and _ready(config, previous["run_id"]):
            print(
                f"Ready {config.environment_id}: web/worker already running; http://127.0.0.1:{config.web_port}"
            )
            return
        if active:
            raise OperationError(
                "Existing execution is not ready; stop the owned instance before restarting"
            )
        _start_attempt(config, disposable=disposable)


def _start_attempt(config: RuntimeConfig, *, disposable: bool) -> None:
    deadline = time.monotonic() + max(0.5, config.startup_timeout - 2)
    existing = running_containers(config)
    known = container_ids(config)
    for identifier in network_ids(config):
        verify_network(identifier, config, known)
    for port in [config.web_port, *([] if existing else [config.pg_port, config.waha_port])]:
        _check_port(port)
    config = _setup(config, str(uuid.uuid4()))
    manifest: Manifest = {
        "environment_id": config.environment_id,
        "checkout": str(config.root),
        "run_id": config.run_id,
        "ports": {
            "web": config.web_port,
            "pg": config.pg_port,
            "waha": config.waha_port,
            "ai": config.ai_port,
        },
        "processes": [],
        "containers": [],
        "disposable": disposable and config.environment == "eval",
        "session_kind": "synthetic" if disposable else "unknown",
        "status": "starting",
    }
    write_manifest(config.directory, manifest)
    try:
        compose(config, ["up", "-d", "--pull", "never"])
        manifest["containers"] = container_ids(config)
        _assert_manifest(manifest, config)
        _wait_database(config, deadline)
        call_command("migrate", verbosity=0)
        _start_optional_inference(config, manifest)
        from garimpei.infra.worker.probe_service import begin_run

        begin_run(config, config.run_id)
        _spawn(config, manifest)
        _wait_ready(config, manifest, deadline)
    except Exception:
        _rollback_attempt(config, manifest, existing)
        raise
    manifest["status"] = "ready"
    write_manifest(config.directory, manifest)
    print(f"Ready {config.environment_id}: web/worker ready; http://127.0.0.1:{config.web_port}")


def _wait_ready(config: RuntimeConfig, manifest: Manifest, deadline: float) -> None:
    while time.monotonic() < deadline:
        if not all(is_live(process) for process in manifest["processes"]):
            raise OperationError(
                "Web/worker: process exited before readiness; inspect private logs"
            )
        if _ready(config, config.run_id):
            return
        time.sleep(0.2)
    raise OperationError("Readiness timeout: database, migrations, worker or WAHA unavailable")


def _rollback_attempt(config: RuntimeConfig, manifest: Manifest, existing: set[str]) -> None:
    for process in manifest["processes"]:
        stop_process(process, config.root, config.shutdown_timeout)
    created = [identifier for identifier in container_ids(config) if identifier not in existing]
    stop_containers(config, created)
    manifest["containers"] = container_ids(config)
    manifest["status"] = "failed"
    write_manifest(config.directory, manifest)


def stop(config: RuntimeConfig, *, clean: bool = False) -> None:
    with instance_lock(config.directory):
        manifest = read_manifest(config.directory)
        if clean and (
            not manifest
            or config.environment != "eval"
            or not manifest["disposable"]
            or manifest["session_kind"] != "synthetic"
        ):
            raise ConfigurationError(
                "--clean: expected owned disposable eval with synthetic session marker"
            )
        if manifest is None:
            print(f"Stopped {config.environment_id}: no active resources")
            return
        _verify_stop_ownership(manifest, config, clean=clean)
        _mark_stopped(config, manifest)
        results = [
            stop_process(process, config.root, config.shutdown_timeout)
            for process in manifest["processes"]
        ]
        stop_containers(config, manifest["containers"])
        from garimpei.infra.runtime.inference_runtime import release_configured_inference

        release_configured_inference(config)
        manifest["status"] = "stopped"
        write_manifest(config.directory, manifest)
        if not all(results):
            raise OperationError(
                "Shutdown incomplete: owned process exceeded timeout; task completion is unknown"
            )
        if clean:
            _clean(config, manifest)
        print(
            f"{'Cleaned' if clean else 'Stopped'} {config.environment_id}: owned web/worker and services; {'disposable data removed' if clean else 'database, volumes and session retained'}"
        )


def _mark_stopped(config: RuntimeConfig, manifest: Manifest) -> None:
    if not any(is_live(process) for process in manifest["processes"]):
        return
    _setup(config, manifest["run_id"])
    from garimpei.infra.worker.probe_service import end_run

    try:
        end_run(config)
    except DatabaseError:
        print("Database unavailable: control chain cannot renew without confirmed current state")
    finally:
        connection.close()


def _clean(config: RuntimeConfig, manifest: Manifest) -> None:
    if manifest["status"] != "stopped":
        raise ConfigurationError("--clean: expected stopped disposable instance")
    _verify_synthetic_session(config, manifest)
    networks = network_ids(config)
    for identifier in networks:
        verify_network(identifier, config, manifest["containers"])
    prefix = "garimpei-" + config.environment_id
    volumes = docker(
        [
            "volume",
            "ls",
            "-q",
            "--filter",
            "label=com.garimpei.environment=" + config.environment_id,
        ],
        config,
    ).splitlines()
    for volume in volumes:
        labels = json.loads(
            docker(["volume", "inspect", "--format", "{{json .Labels}}", volume], config)
        )
        if labels.get("com.garimpei.checkout") != str(config.root) or not volume.startswith(
            prefix + "_"
        ):
            raise OperationError("Volume ownership: expected current checkout and Compose project")
    if manifest["containers"]:
        docker(["rm", *manifest["containers"]], config)
    if networks:
        docker(["network", "rm", *networks], config)
    if volumes:
        docker(["volume", "rm", *volumes], config)
    (config.directory / "manifest.json").unlink()


def _verify_stop_ownership(manifest: Manifest, config: RuntimeConfig, *, clean: bool) -> None:
    try:
        _assert_manifest(manifest, config)
    except OperationError:
        if clean:
            raise ConfigurationError(
                "--clean: expected verified ownership of every resource"
            ) from None
        raise


def _verify_synthetic_session(config: RuntimeConfig, manifest: Manifest) -> None:
    waha = [
        identifier
        for identifier in manifest["containers"]
        if docker(
            [
                "inspect",
                "--format",
                '{{index .Config.Labels "com.docker.compose.service"}}',
                identifier,
            ],
            config,
        )
        == "waha"
    ]
    if len(waha) != 1:
        raise ConfigurationError("--clean: expected exactly one owned synthetic WAHA volume")
    with tempfile.TemporaryDirectory(prefix="session-check-", dir=config.directory) as temporary:
        docker(["cp", waha[0] + ":/app/.sessions/.", temporary], config)
        _check_session_files(Path(temporary))


def _check_session_files(directory: Path) -> None:
    allowed = {
        "garimpei-synthetic-marker",
        "gows/waha.sqlite3",
        "gows/waha.sqlite3-wal",
        "gows/waha.sqlite3-shm",
    }
    files = {str(path.relative_to(directory)) for path in directory.rglob("*") if path.is_file()}
    if not files <= allowed or "gows/waha.sqlite3" not in files:
        raise ConfigurationError(
            "--clean: unknown or real session files; expected synthetic session only"
        )
    with sqlite3.connect(f"file:{directory / 'gows/waha.sqlite3'}?mode=ro", uri=True) as database:
        counts = [
            database.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            for table in ("me", "session_worker", "apps")
        ]
    if any(counts):
        raise ConfigurationError("--clean: real or unknown session metadata; preservation required")


def migrate(config: RuntimeConfig, arguments: list[str]) -> int:
    valid = arguments in [["--check"], ["--apply"]]
    make = len(arguments) == 2 and arguments[0] == "--make"
    if not valid and not make:
        raise ConfigurationError(
            "migrate-dev: expected --check, --apply or --make <snake_case_name>"
        )
    if make and (
        not arguments[1].isascii()
        or not arguments[1].replace("_", "").isalnum()
        or not arguments[1][0].isalpha()
    ):
        raise ConfigurationError(
            f"Migration name {arguments[1]!r}: expected snake_case_name starting with a letter"
        )
    manifest = read_manifest(config.directory)
    if manifest is None:
        raise ConfigurationError("Migration: expected an owned initialized instance manifest")
    _assert_manifest(manifest, config)
    environment = process_environment(config, manifest["run_id"])
    command = [sys.executable, str(config.root / "apps/backend/manage.py")]
    command += (
        ["makemigrations", "runtime", "--name", arguments[1]]
        if make
        else ["migrate", *(["--check"] if arguments == ["--check"] else ["--noinput"])]
    )
    result = subprocess.run(
        command, cwd=config.root / "apps/backend", env=environment, capture_output=True
    )
    print(
        "Migration created locally; database not applied"
        if make and result.returncode == 0
        else "Schema up to date"
        if result.returncode == 0
        else "Migrations pending or database unavailable"
    )
    return 0 if result.returncode == 0 else 1


def _start_optional_inference(config: RuntimeConfig, manifest: Manifest) -> None:
    from garimpei.main import start_configured_inference

    try:
        identifier = start_configured_inference()
        if identifier is not None:
            manifest["inference_container"] = identifier
    except Exception:
        print("AI unavailable: base web/worker remain independent; inspect AI diagnostics")
    finally:
        manifest["containers"] = container_ids(config)
        write_manifest(config.directory, manifest)
