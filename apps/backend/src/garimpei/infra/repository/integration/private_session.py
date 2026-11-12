import json
import os
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from garimpei.domain.integration.values import FacebookSession


def write_session(directory: Path, revision: int, value: FacebookSession) -> Path:
    private_directory(directory)
    path = directory / f"facebook-{revision}-{uuid4().hex}.json"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump({"cookies": [asdict(item) for item in value.cookies], "origins": []}, output)
        output.flush()
        os.fsync(output.fileno())
    return path


def private_directory(directory: Path) -> None:
    try:
        directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    except FileExistsError:
        if directory.is_symlink() or not directory.is_dir() or directory.stat().st_mode & 0o077:
            raise PermissionError("Expected an existing private directory with mode 0700") from None


def current_path(directory: Path, filename: str) -> Path | None:
    if not filename:
        return None
    path = directory / filename
    if path.parent != directory or path.is_symlink() or not path.is_file():
        return None
    if path.stat().st_mode & 0o077:
        return None
    return path
