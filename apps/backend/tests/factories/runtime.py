from __future__ import annotations

import json
import os
import secrets
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import psycopg

from garimpei.config.env import RuntimeConfig, load_config
from garimpei.infra.runtime.manifest import Manifest
from garimpei.infra.runtime.processes import verify_process


@dataclass
class FoundationInstance:
    root: Path
    private_file: Path

    @property
    def environment(self) -> dict[str, str]:
        return dict(
            os.environ,
            GARIMPEI_ENV_FILE=str(self.private_file),
            DJANGO_SETTINGS_MODULE="garimpei.config.settings",
        )

    @property
    def config(self) -> RuntimeConfig:
        return load_config({"GARIMPEI_ENV_FILE": str(self.private_file)}, root=self.root)

    @property
    def manifest(self) -> Manifest:
        return cast(Manifest, json.loads((self.config.directory / "manifest.json").read_text()))

    def command(self, *arguments: str, timeout: int = 90) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(arguments),
            cwd=self.root,
            env=self.environment,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def http(
        self, path: str, *, method: str = "GET", host: str = "127.0.0.1"
    ) -> tuple[int, dict[str, object], str]:
        request = Request(
            f"http://127.0.0.1:{self.config.web_port}{path}", method=method, headers={"Host": host}
        )
        try:
            with urlopen(request, timeout=10) as response:
                body = response.read().decode()
                return response.status, dict(response.headers), body
        except HTTPError as error:
            return error.code, dict(error.headers), error.read().decode()

    def database(self) -> psycopg.Connection[tuple[object, ...]]:
        deadline = time.monotonic() + 10
        while True:
            try:
                return psycopg.connect(self.config.database_url, autocommit=True, connect_timeout=2)
            except psycopg.OperationalError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)

    def shell(self, code: str) -> subprocess.CompletedProcess[str]:
        return self.command(
            "uv",
            "run",
            "--project",
            "apps/backend",
            "--frozen",
            "--no-sync",
            "python",
            "apps/backend/manage.py",
            "shell",
            "-c",
            code,
        )


def prepare_instance(root: Path, directory: Path, identity: str) -> FoundationInstance:
    file = directory / f"{identity}.env"
    values = {
        "GARIMPEI_ENV": "eval",
        "GARIMPEI_INSTANCE": identity,
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(40),
        "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
        "WAHA_API_KEY": secrets.token_urlsafe(32),
        "GARIMPEI_STARTUP_TIMEOUT_SECONDS": "60",
    }
    file.write_text("".join(key + "=" + value + "\n" for key, value in values.items()))
    file.chmod(0o600)
    return FoundationInstance(root, file)


def prepare_checkout_copy(root: Path, directory: Path) -> Path:
    copy = directory / "checkout"
    backend = copy / "apps/backend"
    shutil.copytree(
        root / "apps/backend",
        backend,
        ignore=shutil.ignore_patterns(
            ".venv",
            ".mypy_cache",
            ".ruff_cache",
            ".pytest_cache",
            ".import_linter_cache",
            "__pycache__",
            "dist",
            ".test-static",
        ),
    )
    result = subprocess.run(
        ["cp", "-a", "--reflink=auto", str(root / "apps/backend/.venv"), str(backend / ".venv")],
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError("Failed to prepare isolated Python environment copy")
    shutil.copytree(root / "scripts", copy / "scripts")
    shutil.copyfile(root / "compose.yaml", copy / "compose.yaml")
    return copy


def pause_worker(instance: FoundationInstance) -> int:
    owner = next(
        record for record in instance.manifest["processes"] if "runworker" in record["command"]
    )
    verify_process(owner, instance.config.root)
    group = int(owner["pgid"])
    deadline = time.monotonic() + 10
    # SIGSTOP must not freeze a publication transaction that a shell assertion needs.
    with instance.database() as database:
        while time.monotonic() < deadline:
            os.killpg(group, signal.SIGSTOP)
            time.sleep(0.05)
            try:
                idle = _transactions_idle(database)
            except BaseException:
                os.killpg(group, signal.SIGCONT)
                raise
            if idle:
                return group
            os.killpg(group, signal.SIGCONT)
            time.sleep(0.02)
    raise AssertionError("Owned worker did not reach a transaction-free pause point")


def _transactions_idle(database: psycopg.Connection[tuple[object, ...]]) -> bool:
    row = database.execute("""SELECT count(*) FROM pg_stat_activity
        WHERE datname=current_database() AND pid<>pg_backend_pid()
        AND xact_start IS NOT NULL""").fetchone()
    return row is not None and row[0] == 0


def resume_worker(group: int) -> None:
    os.killpg(group, signal.SIGCONT)
