import fcntl
import json
from pathlib import Path

from garimpei.config.env import InferenceSettings
from garimpei.domain.inference.errors import InferenceError

# Five bounded part responses, coverage, source text and <=721 GPU samples per part.
# Conservative reservation includes PostgreSQL JSON/row overhead; no result is pruned implicitly.
REQUEST_RESERVATION = 2097152


def reserved_bytes(directory: Path) -> int:
    file = directory / "admission-reservations.json"
    if not file.exists():
        return 0
    try:
        values = json.loads(file.read_text())
    except (OSError, ValueError):
        raise InferenceError("capacity_limit", 503) from None
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise InferenceError("capacity_limit", 503)
    return len(values) * REQUEST_RESERVATION


class LocalQuota:
    def __init__(self, settings: InferenceSettings) -> None:
        self._settings = settings

    def reserve(self, signature: str) -> None:
        folder = self._settings.directory
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (folder / "disk.lock").open("a+") as guard:
            fcntl.flock(guard, fcntl.LOCK_EX)
            self._reserve_locked(signature)

    def _reserve_locked(self, signature: str) -> None:
        folder = self._settings.directory
        file = folder / "admission-reservations.json"
        used = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
        reserved = reserved_bytes(folder)
        values = json.loads(file.read_text()) if file.exists() else []
        if signature in values:
            return
        if used + reserved + REQUEST_RESERVATION > self._settings.disk_limit:
            raise InferenceError("capacity_limit", 409)
        values.append(signature)
        temporary = file.with_suffix(".tmp")
        temporary.write_text(json.dumps(values) + "\n")
        temporary.chmod(0o600)
        temporary.replace(file)
