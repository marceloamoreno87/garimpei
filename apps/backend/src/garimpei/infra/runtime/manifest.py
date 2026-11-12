import fcntl
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import NotRequired, TypedDict, cast


class ProcessRecord(TypedDict):
    pid: int
    pgid: int
    created: float
    command: list[str]
    cwd: str


class Manifest(TypedDict):
    environment_id: str
    checkout: str
    run_id: str
    ports: dict[str, int]
    processes: list[ProcessRecord]
    containers: list[str]
    disposable: bool
    session_kind: str
    status: str
    inference_container: NotRequired[str]


class OperationError(RuntimeError):
    """Only fixed diagnostics and nonsecret resource identities cross CLI."""


def read_manifest(directory: Path) -> Manifest | None:
    file = directory / "manifest.json"
    if not file.exists():
        return None
    try:
        return cast(Manifest, json.loads(file.read_text()))
    except (ValueError, OSError):
        raise OperationError("Manifest: expected valid owned JSON metadata") from None


def write_manifest(directory: Path, data: Manifest) -> None:
    file = directory / "manifest.tmp"
    file.write_text(json.dumps(data, indent=2) + "\n")
    file.chmod(0o600)
    file.replace(directory / "manifest.json")


@contextmanager
def instance_lock(directory: Path) -> Iterator[None]:
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory.chmod(0o700)
    with (directory / "operation.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise OperationError("Instance lock: another operation is active") from None
        lock.seek(0)
        lock.truncate()
        lock.write(json.dumps({"pid": os.getpid()}))
        lock.flush()
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
