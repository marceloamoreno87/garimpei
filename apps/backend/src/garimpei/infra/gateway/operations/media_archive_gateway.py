"""Capture immutable protected media under durable F14 pins, never raw access URLs."""

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import cast
from uuid import UUID

from django.db import DatabaseError, connection, connections
from django.utils import timezone

from garimpei.domain.media.errors import MediaError
from garimpei.domain.media.media import AnalysisMedia, MediaFile
from garimpei.infra.gateway.media.local_store import LocalMediaStore
from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.infra.repository.media.postgres_repository import PostgresMediaRepository


class MediaArchiveGateway:
    def __init__(self, repository: PostgresMediaRepository, store: LocalMediaStore) -> None:
        self._repository, self._store = repository, store

    def pin(self, execution: str) -> tuple[AnalysisMedia, ...]:
        return _separate_connection(
            lambda: self._repository.protected_versions(execution, timezone.now())
        )

    def release(self, references: tuple[AnalysisMedia, ...]) -> None:
        _separate_connection(lambda: self._release(references))

    def _release(self, references: tuple[AnalysisMedia, ...]) -> None:
        for reference in references:
            self._repository.release(reference.reference_id, timezone.now())

    def capture(
        self, references: tuple[AnalysisMedia, ...], tables: dict[str, bytes]
    ) -> tuple[dict[str, bytes], dict[str, object]]:
        assets = _asset_rows(tables)
        required = _required_assets(tables, assets)
        pinned = {str(reference.photo.version_id) for reference in references}
        if not required.issubset(pinned):
            raise ArchiveInvalid("backup_media_pin_incomplete")
        files: dict[str, bytes] = {}
        descriptors: list[dict[str, object]] = []
        for identity in sorted(required):
            additions, descriptor = self._capture_asset(identity, assets[identity])
            files.update(additions)
            descriptors.append(descriptor)
        return files, {"protected_media": descriptors, "unprotected_media_bytes_excluded": True}

    def _capture_asset(
        self, identity: str, row: dict[str, object]
    ) -> tuple[dict[str, bytes], dict[str, object]]:
        file = _file(identity, row, thumbnail=False)
        name = f"media/{identity}/original"
        files = {name: _read_media(self._store, file)}
        descriptor: dict[str, object] = {"id": identity, "original": name, "key": file.key}
        if row["thumbnail_state"] == "ready":
            thumbnail = _file(identity, row, thumbnail=True)
            name = f"media/{identity}/thumbnail"
            files[name], descriptor["thumbnail"] = _read_media(self._store, thumbnail), name
        return files, descriptor

    def validate(self, metadata: dict[str, object], files: dict[str, bytes]) -> None:
        assets = _asset_rows(files)
        required = _required_assets(files, assets)
        descriptors = _descriptors(metadata)
        if set(descriptors) != required:
            raise ArchiveInvalid("backup_media_coverage_incomplete")
        expected: set[str] = set()
        for identity, descriptor in descriptors.items():
            expected.update(_validate_asset(identity, assets[identity], descriptor, files))
        if {name for name in files if name.startswith("media/")} != expected:
            raise ArchiveInvalid("backup_media_files_mismatch")

    def restore(self, metadata: dict[str, object], files: dict[str, bytes]) -> set[str]:
        assets, descriptors = _asset_rows(files), _descriptors(metadata)
        for identity, descriptor in descriptors.items():
            self._restore_asset(identity, assets[identity], descriptor, files)
        return set(assets) - set(descriptors)

    def _restore_asset(
        self,
        identity: str,
        row: dict[str, object],
        descriptor: dict[str, object],
        files: dict[str, bytes],
    ) -> None:
        self._store.restore(
            _file(identity, row, thumbnail=False), files[str(descriptor["original"])]
        )
        if "thumbnail" in descriptor:
            self._store.restore(
                _file(identity, row, thumbnail=True), files[str(descriptor["thumbnail"])]
            )


def _separate_connection[T](operation: Callable[[], T]) -> T:
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="backup-media-pins") as executor:
        return executor.submit(_owned_connection, operation).result(timeout=60)


def _owned_connection[T](operation: Callable[[], T]) -> T:
    try:
        _bounded_database()
        return operation()
    except (MediaError, DatabaseError):
        raise ArchiveInvalid("backup_media_unavailable") from None
    finally:
        connections.close_all()


def _rows(files: dict[str, bytes], name: str) -> list[dict[str, object]]:
    return [cast(dict[str, object], json.loads(line)) for line in files[name].splitlines()]


def _asset_rows(files: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {
        str(row["pk"]): cast(dict[str, object], row["fields"])
        for row in _rows(files, "runtime.mediaasset.jsonl")
    }


def _required_assets(files: dict[str, bytes], assets: dict[str, dict[str, object]]) -> set[str]:
    tracked = {
        str(row["pk"])
        for row in _rows(files, "runtime.listing.jsonl")
        if cast(dict[str, object], row["fields"])["media_tracking_active"] is True
    }
    pinned = {
        str(cast(dict[str, object], row["fields"])["asset"])
        for row in _rows(files, "runtime.mediareference.jsonl")
        if cast(dict[str, object], row["fields"])["released_at"] is None
    }
    return {
        identity
        for identity, fields in assets.items()
        if fields["state"] == "available"
        and (str(fields["listing"]) in tracked or identity in pinned)
    }


def _file(identity: str, row: dict[str, object], *, thumbnail: bool) -> MediaFile:
    return MediaFile(
        UUID(identity),
        str(row["key"]) + (".thumb" if thumbnail else ""),
        "image/webp" if thumbnail else str(row["mime"]),
        str(row["thumbnail_hash"] if thumbnail else row["sha256"]),
        int(str(row["thumbnail_bytes"] if thumbnail else row["byte_count"])),
    )


def _descriptors(metadata: dict[str, object]) -> dict[str, dict[str, object]]:
    values = metadata.get("protected_media")
    if not isinstance(values, list):
        raise ArchiveInvalid("backup_media_manifest_missing")
    result: dict[str, dict[str, object]] = {}
    for value in values:
        if not isinstance(value, dict) or str(value.get("id")) in result:
            raise ArchiveInvalid("backup_media_manifest_invalid")
        result[str(value["id"])] = cast(dict[str, object], value)
    return result


def _validate_asset(
    identity: str, row: dict[str, object], descriptor: dict[str, object], files: dict[str, bytes]
) -> set[str]:
    expected = {f"media/{identity}/original"}
    _validate_content(
        _file(identity, row, thumbnail=False), files.get(f"media/{identity}/original")
    )
    if (
        descriptor.get("original") != f"media/{identity}/original"
        or descriptor.get("key") != row["key"]
    ):
        raise ArchiveInvalid("backup_media_version_mismatch")
    if row["thumbnail_state"] == "ready":
        _validate_content(
            _file(identity, row, thumbnail=True), files.get(f"media/{identity}/thumbnail")
        )
        if descriptor.get("thumbnail") != f"media/{identity}/thumbnail":
            raise ArchiveInvalid("backup_media_thumbnail_mismatch")
        expected.add(f"media/{identity}/thumbnail")
    return expected


def _validate_content(file: MediaFile, data: bytes | None) -> None:
    import hashlib

    if (
        data is None
        or len(data) != file.byte_count
        or hashlib.sha256(data).hexdigest() != file.sha256
    ):
        raise ArchiveInvalid("backup_media_bytes_missing_or_corrupt")


def _read_media(store: LocalMediaStore, file: MediaFile) -> bytes:
    try:
        return store.read(file)
    except MediaError:
        raise ArchiveInvalid("backup_media_unavailable") from None


def _bounded_database() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SET lock_timeout = '20s'")
        cursor.execute("SET statement_timeout = '60s'")
