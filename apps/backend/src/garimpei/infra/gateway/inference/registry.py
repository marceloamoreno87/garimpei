import fcntl
import hashlib
import json
from pathlib import Path
from typing import cast

from garimpei.config.env import InferenceSettings
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.request import ImageReference
from garimpei.infra.gateway.inference.quota import reserved_bytes


def registered(settings: InferenceSettings, identity: str) -> dict[str, object]:
    try:
        rows = json.loads((settings.directory / "input-registry.json").read_text())
        value = rows[identity]
    except (OSError, ValueError, KeyError, TypeError):
        raise InferenceError("image_not_registered") from None
    if not isinstance(value, dict):
        raise InferenceError("image_not_registered")
    return cast(dict[str, object], value)


def register_file(
    settings: InferenceSettings, source: Path, metadata: dict[str, object]
) -> ImageReference:
    reference = ImageReference(
        str(metadata["id"]), int(str(metadata["revision"])), str(metadata["sha256"])
    )
    if not metadata.get("authorization") or source.is_symlink() or source.stat().st_size > 10485760:
        raise InferenceError("invalid_image_content")
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference.sha256:
        raise InferenceError("invalid_image_content")
    folder = settings.directory
    (folder / "sources").mkdir(parents=True, exist_ok=True, mode=0o700)
    with (folder / "disk.lock").open("a+") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        _register_locked(settings, raw, metadata, reference)
    return reference


def _register_locked(
    settings: InferenceSettings, raw: bytes, metadata: dict[str, object], reference: ImageReference
) -> None:
    folder = settings.directory
    file = folder / "sources" / reference.sha256
    used = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
    if not file.exists() and used + reserved_bytes(folder) + len(raw) > settings.disk_limit:
        raise InferenceError("capacity_limit")
    if not file.exists():
        temporary = file.with_suffix(".tmp")
        temporary.write_bytes(raw)
        temporary.chmod(0o600)
        temporary.replace(file)
    registry = folder / "input-registry.json"
    rows = json.loads(registry.read_text()) if registry.exists() else {}
    rows[reference.id] = metadata
    temporary = registry.with_suffix(".tmp")
    temporary.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(registry)
