import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import UUID

from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.media import MediaClaim, MediaFile, Transfer
from garimpei.domain.media.policy import MediaPolicy


class LocalMediaStore:
    def __init__(self, root: Path, policy: MediaPolicy, environment_id: str) -> None:
        self.root, self._policy, self._owner = root, policy, environment_id

    def _path(self, key: str) -> Path:
        if not re.fullmatch(r"[a-f0-9-]{36}/[a-f0-9]{64}(?:\.thumb)?", key):
            raise MediaError("media_file_unavailable")
        result = self.root / key
        if result.is_symlink() or result.parent.is_symlink() or self.root.is_symlink():
            raise MediaError("media_file_unavailable")
        return result

    def put(self, claim: MediaClaim, content: Transfer) -> str:
        key = f"{claim.listing_id}/{hashlib.sha256((claim.photo_key + content.sha256).encode()).hexdigest()}"
        self._atomic(key, content.data)
        return key

    def _atomic(self, key: str, data: bytes) -> None:
        destination = self._path(key)
        self._ensure_owner()
        destination.parent.mkdir(mode=0o700, exist_ok=True)
        if shutil.disk_usage(self.root).free < len(data) + self._policy.min_free_bytes:
            raise MediaError("media_disk_reserve")
        fd, name = tempfile.mkstemp(prefix=".media-", dir=destination.parent)
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.replace(name, destination)
            directory = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(name).unlink(missing_ok=True)

    def used_bytes(self) -> int:
        if self.root.exists():
            self._ensure_owner()
        return (
            sum(p.stat().st_size for p in self.root.glob("*/*") if p.is_file())
            if self.root.exists()
            else 0
        )

    def read(self, file: MediaFile) -> bytes:
        self._verify_owner()
        try:
            data = self._path(file.key).read_bytes()
        except OSError:
            raise MediaError("MEDIA_FILE_UNAVAILABLE") from None
        if len(data) != file.byte_count or hashlib.sha256(data).hexdigest() != file.sha256:
            raise MediaError("MEDIA_FILE_UNAVAILABLE")
        return data

    def restore(self, file: MediaFile, data: bytes) -> None:
        """Restore an exact verified immutable version into this instance's owned media root."""
        if len(data) != file.byte_count or hashlib.sha256(data).hexdigest() != file.sha256:
            raise MediaError("MEDIA_BACKUP_HASH_INVALID")
        if len(data) > self._policy.max_file_bytes:
            raise MediaError("MEDIA_BACKUP_FILE_LIMIT")
        self._atomic(file.key, data)

    def derive(self, claim: MediaClaim, original: MediaFile) -> MediaFile:
        data = self.read(original)
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "garimpei.infra.gateway.media.thumbnail",
                    str(self._policy.thumb_edge),
                ],
                input=data,
                capture_output=True,
                timeout=20,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise MediaError("media_thumbnail_timeout") from None
        if result.returncode or len(result.stdout) > self._policy.max_file_bytes:
            raise MediaError("media_thumbnail_failed")
        key = original.key + ".thumb"
        self._atomic(key, result.stdout)
        return MediaFile(
            claim.asset_id or UUID(int=0),
            key,
            "image/webp",
            hashlib.sha256(result.stdout).hexdigest(),
            len(result.stdout),
        )

    def remove(self, file: MediaFile) -> None:
        self._ensure_owner()
        self._path(file.key).unlink(missing_ok=True)
        self._path(file.key + ".thumb").unlink(missing_ok=True)

    def reconcile_orphans(self, known_keys: set[str], lease_seconds: int) -> int:
        if not self.root.exists():
            return 0
        self._ensure_owner()
        cutoff = time.time() - lease_seconds
        candidates = tuple(
            p
            for p in self.root.glob("*/*")
            if p.is_file()
            and not p.is_symlink()
            and not p.parent.is_symlink()
            and re.fullmatch(r"[a-f0-9-]{36}", p.parent.name)
            and re.fullmatch(r"[a-f0-9]{64}(?:\.thumb)?|\.media-.+", p.name)
            and p.stat().st_mtime < cutoff
            and str(p.relative_to(self.root)) not in known_keys
        )
        for file in candidates:
            file.unlink(missing_ok=True)
        return len(candidates)

    def _verify_owner(self) -> None:
        marker = self.root / ".garimpei-media-owner"
        if marker.is_symlink():
            raise MediaError("media_storage_owner_conflict")
        if marker.exists() and marker.read_text() != self._owner:
            raise MediaError("media_storage_owner_conflict")

    def _ensure_owner(self) -> None:
        marker = self.root / ".garimpei-media-owner"
        self._verify_owner()
        if (
            not marker.exists()
            and self.root.exists()
            and any(self.root.iterdir())
            and self.root.name != self._owner
        ):
            raise MediaError("media_storage_owner_required")
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "w") as output:
                output.write(self._owner)
        except FileExistsError:
            self._verify_owner()
        self.root.chmod(0o700)
