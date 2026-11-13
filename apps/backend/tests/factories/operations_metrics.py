"""Sample only the nested eval instance used by a measured failure/control pair."""

import hashlib
import json
import platform
import shutil
import time
from contextlib import AbstractContextManager
from importlib.metadata import version
from pathlib import Path
from threading import Event, Thread
from types import TracebackType

import psycopg

from tests.factories.operations_storage_metrics import read_storage_metrics
from tests.factories.runtime import FoundationInstance


class InstanceMeasurements(AbstractContextManager["InstanceMeasurements"]):
    def __init__(self, instance: FoundationInstance, destination: Path, *, mode: str) -> None:
        if instance.config.environment != "eval":
            raise ValueError("Measurements require an owned eval instance")
        if mode not in {"control", "fault"}:
            raise ValueError("Expected control or fault measurement mode")
        self.mode = mode
        self.instance = instance
        self.destination = destination
        self.finished = Event()
        self.thread = Thread(target=self._observe, daemon=True)
        self.started = 0.0
        self.samples: list[dict[str, int]] = []
        self.failures = 0
        self.postgres_version = ""
        self.observed: dict[str, int] = {}

    def __enter__(self) -> "InstanceMeasurements":
        self.started = time.monotonic()
        self.thread.start()
        return self

    def _observe(self) -> None:
        while not self.finished.is_set():
            self._sample()
            self.finished.wait(0.1)

    def _sample(self) -> None:
        try:
            with psycopg.connect(
                self.instance.config.database_url, connect_timeout=1, autocommit=True
            ) as connection:
                row = connection.execute(
                    "SELECT pg_database_size(current_database()), version(), "
                    "(SELECT count(*) FROM procrastinate_jobs WHERE status IN ('todo','doing'))"
                ).fetchone()
            assert row is not None
            self.postgres_version = str(row[1])
            self.samples.append(
                {
                    "database_bytes": int(row[0]),
                    "pending_jobs": int(row[2]),
                    **read_storage_metrics(self.instance),
                    "free_bytes": shutil.disk_usage(self.instance.root).free,
                }
            )
        except (OSError, psycopg.Error):
            self.failures += 1

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.finished.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise RuntimeError("Owned measurement thread did not terminate")
        if exception_type is not None:
            return
        if not self.samples:
            raise RuntimeError("No owned database measurements collected")
        report = {
            "mode": self.mode,
            "seconds": time.monotonic() - self.started,
            "sample_count": len(self.samples),
            "sample_errors": self.failures,
            "sampled_peak_database_bytes": max(row["database_bytes"] for row in self.samples),
            "sampled_peak_runtime_bytes": max(row["runtime_bytes"] for row in self.samples),
            "minimum_free_bytes": min(row["free_bytes"] for row in self.samples),
            "max_pending_jobs": max(row["pending_jobs"] for row in self.samples),
            "sampled_peak_media_bytes": max(row["media_bytes"] for row in self.samples),
            "sampled_peak_backup_bytes": max(row["backup_bytes"] for row in self.samples),
            "max_oldest_pending_age_seconds": max(
                row["oldest_pending_age_seconds"] for row in self.samples
            ),
            "sampled_peak_data_bytes": max(
                row["database_bytes"] + row["media_bytes"] + row["runtime_bytes"]
                for row in self.samples
            ),
            "postgres_version": self.postgres_version,
            "versions": {
                name: version(name)
                for name in ("Django", "psycopg", "procrastinate", "playwright", "pillow")
            },
            "python_version": platform.python_version(),
            "runtime_code_sha256": _source_digest(self.instance.root / "apps/backend/src"),
            "measurement_code_sha256": _source_digest(self.instance.root / "apps/backend/tests"),
            "lock_sha256": hashlib.sha256(
                (self.instance.root / "apps/backend/uv.lock").read_bytes()
            ).hexdigest(),
            "sampling_seconds": 0.1,
            "scope": "nested eval database and runtime; sampled logical-byte peaks include configured media/backups/export/temporary files and runtime; exclude container filesystem allocation",
            **self.observed,
        }
        self.destination.write_text(json.dumps(report, indent=2) + "\n")


def workload_signature(payload: object) -> int:
    """Comparable digest of synthetic inputs without publishing their bodies."""
    return int(hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), 16)


def _source_digest(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*.py")):
        digest.update(str(path.relative_to(directory)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
