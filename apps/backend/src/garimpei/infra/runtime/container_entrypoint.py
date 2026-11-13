"""Container process entry: migrations are serialized separately from web/worker."""

import hashlib
import os
import shutil
import sys
from pathlib import Path

import django
from django.core.management import call_command
from django.db import connection

from garimpei.config.env import RuntimeConfig, configure_django, load_config


def main(arguments: list[str]) -> int:
    configure_django()
    django.setup()
    operation, *options = arguments or ["web"]
    if operation == "prepare":
        _prepare()
        return 0
    if operation == "web":
        os.execvp(
            "gunicorn",
            [
                "gunicorn",
                "garimpei.config.wsgi:application",
                "--bind",
                "0.0.0.0:8000",
                "--workers",
                "1",
                "--access-logfile",
                "-",
            ],
        )
    if operation == "worker":
        call_command("runworker")
        return 0
    if operation in {"login", "display-test"}:
        from garimpei.infra.runtime.container_login import run_login

        return run_login(operation == "display-test")
    if operation == "manage":
        call_command(*options)
        return 0
    if operation == "ready":
        from garimpei.main import build_readiness

        result = build_readiness().execute()
        return 0 if result.ready else 1
    raise ValueError("Container command: expected prepare, web, worker, manage or ready")


def _prepare() -> None:
    from garimpei.infra.worker.probe_service import begin_run

    _copy_tokenizer()
    # A session-level advisory lock survives migration transactions.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(230023)")
        try:
            call_command("migrate", interactive=False, verbosity=0)
            call_command("collectstatic", interactive=False, verbosity=0)
            config = load_config()
            begin_run(config, config.run_id)
            _manifest(config)
        finally:
            cursor.execute("SELECT pg_advisory_unlock(230023)")


def _manifest(config: "RuntimeConfig") -> None:
    from garimpei.config.env import disposable_container
    from garimpei.infra.runtime.manifest import write_manifest

    disposable = disposable_container()
    write_manifest(
        config.directory,
        {
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
            "disposable": disposable,
            "session_kind": "synthetic" if disposable else "unknown",
            "status": "ready",
        },
    )


def _copy_tokenizer() -> None:
    from garimpei.config.env import load_inference_settings
    from garimpei.infra.gateway.inference.input_preparer import read_lock

    settings = load_inference_settings()
    source = Path("/app/artifacts/tokenizer.json")
    expected = read_lock(settings.model_lock)["tokenizer"]
    if (
        not isinstance(expected, dict)
        or hashlib.sha256(source.read_bytes()).hexdigest() != expected["sha256"]
    ):
        raise ValueError("Packaged tokenizer digest mismatch")
    settings.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not settings.tokenizer.exists():
        shutil.copyfile(source, settings.tokenizer)
        settings.tokenizer.chmod(0o600)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
