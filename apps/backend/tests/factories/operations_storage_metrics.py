"""Read public sizes and queue age from one explicitly configured eval instance.

Sizes are logical file bytes sampled at call time, not filesystem allocation or
continuous high-water marks. The caller retains maxima across samples. Backup
traversal includes completed copies, partial writes and exports in that root.
"""

import os
import stat
from datetime import datetime
from pathlib import Path

import psycopg

from garimpei.config.env import _values
from tests.factories.runtime import FoundationInstance


def read_storage_metrics(instance: FoundationInstance) -> dict[str, int]:
    config = instance.config
    if config.environment != "eval":
        raise ValueError("Storage measurements require an owned eval instance")
    # Explicit values prevent the operator's environment from changing this scope.
    values = _values({"GARIMPEI_ENV_FILE": str(instance.private_file)})
    private = Path.home() / ".local/share/garimpei"
    media = Path(values.get("GARIMPEI_MEDIA_ROOT", str(private / "media" / config.environment_id)))
    backup = Path(
        values.get("GARIMPEI_BACKUP_DIR", str(private / "backups" / config.environment_id))
    )
    sizes = {
        "runtime_bytes": _directory_bytes(config.directory),
        "media_bytes": _directory_bytes(media.expanduser()),
        "backup_bytes": _directory_bytes(backup.expanduser()),
    }
    with psycopg.connect(config.database_url, connect_timeout=1, autocommit=True) as database:
        row = database.execute(
            "SELECT clock_timestamp(), min(pending_since) "
            "FROM runtime_operationalunit WHERE pending > 0"
        ).fetchone()
    if row is None or not isinstance(row[0], datetime):
        raise RuntimeError("Expected queue measurement timestamp")
    since = row[1]
    if since is not None and not isinstance(since, datetime):
        raise RuntimeError("Expected pending queue timestamp or null")
    sizes["oldest_pending_age_seconds"] = (
        max(0, int((row[0] - since).total_seconds())) if since else 0
    )
    return sizes


def _directory_bytes(root: Path) -> int:
    if any(path.is_symlink() for path in (root, *root.parents)):
        raise ValueError("Storage measurement root must not be a symlink")
    if not root.exists():
        return 0
    if not root.is_dir():
        raise ValueError("Storage measurement root must be a directory")
    total = 0
    for directory, children, files in os.walk(root, followlinks=False, onerror=_raise_walk_error):
        children[:] = [name for name in children if not (Path(directory) / name).is_symlink()]
        total += sum(_file_bytes(Path(directory) / name) for name in files)
    return total


def _file_bytes(path: Path) -> int:
    try:
        info = path.lstat()
    except FileNotFoundError:
        # Atomic publication/cleanup may remove a sampled temporary file.
        return 0
    return info.st_size if stat.S_ISREG(info.st_mode) else 0


def _raise_walk_error(error: OSError) -> None:
    raise error
