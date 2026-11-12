"""Private allowlisted archives. Validation never extracts filesystem paths."""

import hashlib
import io
import json
import os
import shutil
import tarfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import UUID


class ArchiveInvalid(Exception):
    pass


class ArchiveGateway:
    def __init__(
        self,
        root: Path,
        *,
        reserve_bytes: int = 1024**3,
        budget_bytes: int = 10 * 1024**3,
        owner: str = "isolated_archive",
    ) -> None:
        self.root, self._reserve, self._budget = root, reserve_bytes, budget_bytes
        self._owner = owner

    def _prepare(self, required: int) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.is_symlink():
            raise ArchiveInvalid("archive_directory_invalid")
        self._verify_owner()
        self.root.chmod(0o700)
        used = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
        free = shutil.disk_usage(self.root).free
        if used + required > self._budget or free - required < self._reserve:
            raise ArchiveInvalid("archive_storage_limit")
        for name in ("completed", "partial", "exports"):
            directory = self.root / name
            directory.mkdir(exist_ok=True, mode=0o700)
            if directory.is_symlink():
                raise ArchiveInvalid("archive_directory_invalid")
            directory.chmod(0o700)

    def _verify_owner(self) -> None:
        marker = self.root / ".garimpei-backup-owner"
        if marker.exists():
            if marker.is_symlink() or marker.read_text() != self._owner:
                raise ArchiveInvalid("archive_directory_owner_mismatch")
            return
        if any(self.root.iterdir()):
            raise ArchiveInvalid("archive_directory_not_owned")
        with marker.open("x") as output:
            os.fchmod(output.fileno(), 0o600)
            output.write(self._owner)

    def write(
        self, kind: str, identity: str, metadata: dict[str, object], files: dict[str, bytes]
    ) -> Path:
        if kind not in {"completed", "exports"} or str(UUID(identity)) != identity:
            raise ArchiveInvalid("archive_key_invalid")
        if any(not _safe_name(name) for name in files):
            raise ArchiveInvalid("archive_entry_invalid")
        self._prepare(sum(len(data) for data in files.values()) * 2 + 65536)
        manifest = metadata | {
            "files": {
                name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                for name, data in files.items()
            }
        }
        partial = self.root / "partial" / (identity + ".tar.gz")
        final = self.root / kind / (identity + ".tar.gz")
        started = time.monotonic()
        try:
            with partial.open("xb") as output:
                os.fchmod(output.fileno(), 0o600)
                self._write_tar(output, manifest, files, started)
                output.flush()
                os.fsync(output.fileno())
            self.read(partial)
            if final.exists():
                raise ArchiveInvalid("archive_already_exists")
            partial.replace(final)
            _sync_directory(final.parent)
            return final
        except BaseException:
            partial.unlink(missing_ok=True)
            raise

    @staticmethod
    def _write_tar(
        output: io.BufferedWriter,
        manifest: dict[str, object],
        files: dict[str, bytes],
        started: float,
    ) -> None:
        with tarfile.open(fileobj=output, mode="w:gz") as archive:
            for name, data in files.items():
                _check_timeout(started)
                _add_file(archive, name, data)
            manifest["finished_at"] = datetime.now(UTC).isoformat()
            _add_file(archive, "manifest.json", json.dumps(manifest, sort_keys=True).encode())

    def read(self, path: Path) -> tuple[dict[str, object], dict[str, bytes]]:
        try:
            return self._read_archive(path)
        except (OSError, tarfile.TarError, ValueError, UnicodeError, KeyError, TypeError):
            raise ArchiveInvalid("archive_invalid") from None

    def _read_archive(self, path: Path) -> tuple[dict[str, object], dict[str, bytes]]:
        if path.is_symlink() or not path.is_file():
            raise ArchiveInvalid("archive_file_invalid")
        files: dict[str, bytes] = {}
        total = 0
        started = time.monotonic()
        with tarfile.open(path, mode="r:gz") as archive:
            for member in archive:
                total += member.size
                _validate_member(member, files, total, self._budget, started)
                files[member.name] = _read_member(archive, member)
        manifest = _mapping(json.loads(files.pop("manifest.json")))
        if manifest.get("format_version") != 1:
            raise ArchiveInvalid("archive_version_incompatible")
        expected = _mapping(manifest.get("files"))
        if set(files) != set(expected):
            raise ArchiveInvalid("archive_entry_set_mismatch")
        for name, data in files.items():
            info = _mapping(expected[name])
            if (
                info.get("bytes") != len(data)
                or info.get("sha256") != hashlib.sha256(data).hexdigest()
            ):
                raise ArchiveInvalid("archive_checksum_mismatch")
        return manifest, files

    def resolve(self, key: str) -> Path:
        parts = key.split("/")
        if len(parts) != 2 or parts[0] not in {"completed", "exports"}:
            raise ArchiveInvalid("archive_key_invalid")
        identity = parts[1].removesuffix(".tar.gz")
        if parts[1] != str(UUID(identity)) + ".tar.gz":
            raise ArchiveInvalid("archive_key_invalid")
        path = self.root / key
        if path.resolve().parent != (self.root / parts[0]).resolve() or path.is_symlink():
            raise ArchiveInvalid("archive_key_invalid")
        return path


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ArchiveInvalid("archive_mapping_invalid")
    return cast(dict[str, object], value)


def _safe_name(name: str) -> bool:
    return name.endswith(".jsonl") and "/" not in name and "\\" not in name and ".." not in name


def _validate_member(
    member: tarfile.TarInfo, files: dict[str, bytes], total: int, budget: int, started: float
) -> None:
    if not member.isfile() or (member.name != "manifest.json" and not _safe_name(member.name)):
        raise ArchiveInvalid("archive_entry_invalid")
    if member.name in files or total > budget or len(files) >= 100:
        raise ArchiveInvalid("archive_limits_exceeded")
    if time.monotonic() - started > 300:
        raise ArchiveInvalid("archive_timeout")


def _add_file(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    member = tarfile.TarInfo(name)
    member.size, member.mode = len(data), 0o600
    archive.addfile(member, io.BytesIO(data))


def _sync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def copy_archive(gateway: ArchiveGateway, source: Path, identity: str) -> Path:
    gateway.read(source)
    gateway._prepare(source.stat().st_size)
    partial = gateway.root / "partial" / (str(UUID(identity)) + ".tar.gz")
    target = gateway.root / "exports" / (str(UUID(identity)) + ".tar.gz")
    started = time.monotonic()
    try:
        with source.open("rb") as reader, partial.open("xb") as output:
            os.fchmod(output.fileno(), 0o600)
            _copy_bytes(reader, output, started)
            output.flush()
            os.fsync(output.fileno())
        gateway.read(partial)
        partial.replace(target)
        _sync_directory(target.parent)
        return target
    except BaseException:
        partial.unlink(missing_ok=True)
        raise


def _copy_bytes(reader: io.BufferedReader, output: io.BufferedWriter, started: float) -> None:
    while chunk := reader.read(1024 * 1024):
        if time.monotonic() - started > 300:
            raise ArchiveInvalid("archive_timeout")
        output.write(chunk)


def file_hash(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def _read_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    source = archive.extractfile(member)
    if source is None:
        raise ArchiveInvalid("archive_entry_invalid")
    return source.read(member.size + 1)


def _check_timeout(started: float) -> None:
    if time.monotonic() - started > 300:
        raise ArchiveInvalid("archive_timeout")
