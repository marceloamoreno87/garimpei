import fcntl
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from garimpei.domain.inference.errors import InferenceError


class HostGpuGuard:
    def __init__(self, path: Path, owner: str) -> None:
        self._path, self._owner = path, owner

    def reserve(self) -> bool:
        self._path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self._path.with_suffix(".lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self._path.exists() and self._read() != self._owner:
                return False
            self._path.write_text(json.dumps({"owner": self._owner}) + "\n")
            self._path.chmod(0o600)
            return True

    def owned(self) -> bool:
        return self._path.exists() and self._read() == self._owner

    def release(self) -> None:
        with self._path.with_suffix(".lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self.owned():
                self._path.unlink()

    @contextmanager
    def call(self) -> Iterator[None]:
        if not self.owned():
            raise InferenceError("gpu_unavailable", 503)
        with self._path.with_suffix(".call").open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise InferenceError("execution_unknown", 503) from None
            yield

    def _read(self) -> str:
        try:
            return str(json.loads(self._path.read_text())["owner"])
        except (ValueError, OSError, KeyError):
            raise InferenceError("gpu_unavailable", 503) from None
