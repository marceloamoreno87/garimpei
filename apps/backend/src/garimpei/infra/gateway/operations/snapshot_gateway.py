"""One repeatable-read snapshot, strict schema validation, and transactional restoration."""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import cast

from django.apps import apps
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.management.color import no_style
from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder
from django.db.models import Field, ForeignKey, Max, Model
from django.utils import timezone

from garimpei.domain.media.media import AnalysisMedia
from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.infra.gateway.operations.inference_archive_gateway import InferenceArchiveGateway
from garimpei.infra.gateway.operations.media_archive_gateway import MediaArchiveGateway
from garimpei.infra.gateway.operations.private_fields import (
    sanitize_transient_media,
    validate_private_fields,
)
from garimpei.infra.gateway.operations.restored_media import restore_media_work
from garimpei.infra.gateway.operations.schema import SCHEMA
from garimpei.infra.persistence.listing_models import ListingEvent
from garimpei.infra.persistence.media_models import MediaAsset, MediaReference


def schema_hash() -> str:
    shape = {name: fields for name, (_, fields) in SCHEMA.items()}
    return hashlib.sha256(json.dumps(shape, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class CapturedSnapshot:
    snapshot_at: datetime
    files: dict[str, bytes]
    counts: dict[str, int]
    information: dict[str, object]
    close: Callable[[], None]


class BusinessSnapshotGateway:
    def __init__(
        self,
        media: MediaArchiveGateway | None = None,
        inference: InferenceArchiveGateway | None = None,
    ) -> None:
        self._media, self._inference = media, inference

    def capture(self, execution: str) -> CapturedSnapshot:
        _validate_schema_coverage()
        references: list[AnalysisMedia] = []
        try:
            with transaction.atomic():
                _read_only_snapshot()
                return self._capture_snapshot(execution, references)
        except BaseException:
            self._release(tuple(references))
            raise

    def _capture_snapshot(
        self, execution: str, references: list[AnalysisMedia]
    ) -> CapturedSnapshot:
        files: dict[str, bytes] = {}
        counts: dict[str, int] = {}
        for name, (model, fields) in SCHEMA.items():
            data, count = _capture_table(model, fields)
            files[name + ".jsonl"], counts[name] = data, count
        metadata: dict[str, object] = {
            "migrations": [
                f"{app}.{name}"
                for app, name in sorted(MigrationRecorder(connection).applied_migrations())
            ],
            "covered_event_cursor": ListingEvent.objects.aggregate(value=Max("sequence"))["value"],
            "code_sha256": _code_hash(),
            "protected_media": [],
        }
        if self._media is not None:
            references.extend(self._media.pin(execution))
            media_files, information = self._media.capture(tuple(references), files)
            files.update(media_files)
            metadata.update(information)
        if self._inference is not None:
            prepared, information = self._inference.capture(files)
            files.update(prepared)
            metadata.update(information)
        with connection.cursor() as cursor:
            cursor.execute("SELECT transaction_timestamp()")
            stamp = cursor.fetchone()
        assert stamp is not None
        return CapturedSnapshot(
            cast(datetime, stamp[0]),
            files,
            counts,
            metadata,
            lambda: self._release(tuple(references)),
        )

    def _release(self, references: tuple[AnalysisMedia, ...]) -> None:
        if self._media is not None:
            self._media.release(references)

    def validate(self, metadata: dict[str, object], files: dict[str, bytes]) -> None:
        try:
            self._validate(metadata, files)
        except (ValidationError, ValueError, KeyError, TypeError, UnicodeError, RecursionError):
            raise ArchiveInvalid("archive_record_invalid") from None

    def _validate(self, metadata: dict[str, object], files: dict[str, bytes]) -> None:
        if metadata.get("schema_hash") != schema_hash():
            raise ArchiveInvalid("archive_schema_incompatible")
        expected = {name + ".jsonl" for name in SCHEMA}
        if {name for name in files if name.endswith(".jsonl")} != expected:
            raise ArchiveInvalid("archive_tables_incomplete")
        identities = {name: _identities(name, files[name + ".jsonl"]) for name in SCHEMA}
        identities["runtime.listingevent:id"] = {
            str(row["fields"]["id"])
            for row in _records(files["runtime.listingevent.jsonl"])
            if isinstance(row["fields"], dict)
        }
        try:
            for name in expected:
                _validate_table(name.removesuffix(".jsonl"), files[name], identities)
        except (ValidationError, ValueError, TypeError):
            raise ArchiveInvalid("archive_field_invalid") from None
        if self._media is not None:
            self._media.validate(metadata, files)
        if self._inference is not None:
            self._inference.validate(metadata, files)

    def restore(self, files: dict[str, bytes], metadata: dict[str, object]) -> None:
        for name in SCHEMA:
            _restore_table(name, files[name + ".jsonl"])
        if self._media is not None:
            omitted = self._media.restore(metadata, files)
            MediaAsset.objects.filter(id__in=omitted, state="available").update(
                state="removed", reason="unprotected_bytes_not_in_backup"
            )
        restore_media_work()
        if self._inference is not None:
            self._inference.restore(metadata, files)
        MediaReference.objects.filter(consumer="backup", released_at=None).update(
            released_at=timezone.now()
        )
        # Imported explicit numeric primary keys must not collide with future inserts.
        sequence_sql = connection.ops.sequence_reset_sql(
            no_style(), [model for model, _ in SCHEMA.values()]
        )
        with connection.cursor() as cursor:
            for statement in sequence_sql:
                cursor.execute(statement)

    def is_empty(self) -> bool:
        return not any(model._default_manager.exists() for model, _ in SCHEMA.values())


def _capture_table(model: type[Model], fields: tuple[str, ...]) -> tuple[bytes, int]:
    result = bytearray()
    count = 0
    for row in model._default_manager.order_by(model._meta.pk.name).iterator(chunk_size=100):
        raw = serializers.serialize("json", [row], fields=fields)
        record = json.loads(raw)[0]
        record["fields"] = sanitize_transient_media(record["fields"])
        validate_private_fields(record["fields"])
        result.extend(json.dumps(record, separators=(",", ":")).encode() + b"\n")
        count += 1
    return bytes(result), count


def _records(data: bytes) -> list[dict[str, object]]:
    records = []
    for line in data.splitlines():
        row = json.loads(line)
        if not isinstance(row, dict) or set(row) != {"model", "pk", "fields"}:
            raise ArchiveInvalid("archive_record_invalid")
        validate_private_fields(row["fields"])
        records.append(cast(dict[str, object], row))
    return records


def _identities(name: str, data: bytes) -> set[str]:
    result: set[str] = set()
    for row in _records(data):
        identity = str(SCHEMA[name][0]._meta.pk.to_python(row["pk"]))
        if row["model"] != name or identity in result:
            raise ArchiveInvalid("archive_duplicate_or_unknown_record")
        result.add(identity)
    return result


def _validate_table(name: str, data: bytes, identities: dict[str, set[str]]) -> None:
    model, fields = SCHEMA[name]
    for row in _records(data):
        raw = row["fields"]
        if not isinstance(raw, dict) or set(raw) != set(fields):
            raise ArchiveInvalid("archive_field_set_invalid")
        model._meta.pk.to_python(row["pk"])
        _validate_fields(model, cast(dict[str, object], raw), identities)


def _validate_fields(
    model: type[Model], fields: dict[str, object], identities: dict[str, set[str]]
) -> None:
    for name, value in fields.items():
        _validate_field(model, name, value, identities)


def _validate_field(
    model: type[Model], name: str, value: object, identities: dict[str, set[str]]
) -> None:
    field = model._meta.get_field(name)
    if not isinstance(field, Field):
        raise ArchiveInvalid("archive_field_invalid")
    if value is None and not field.null:
        raise ArchiveInvalid("archive_null_field")
    if isinstance(field, ForeignKey) and field.remote_field is not None:
        _validate_relation(field.remote_field.model, value, identities, field.target_field.name)
        return
    converted = field.to_python(value)
    if converted is not None:
        field.run_validators(converted)


def _validate_relation(
    target: type[Model] | str, value: object, identities: dict[str, set[str]], field_name: str
) -> None:
    if value is None:
        return
    if isinstance(target, str):
        raise ArchiveInvalid("archive_relation_invalid")
    name = target._meta.label_lower
    if field_name != target._meta.pk.name:
        name += ":" + field_name
    if name not in identities or str(value) not in identities[name]:
        raise ArchiveInvalid("archive_relation_missing")


def _restore_table(_name: str, data: bytes) -> None:
    raw = b"[" + b",".join(data.splitlines()) + b"]"
    for record in serializers.deserialize("json", raw):
        record.save()


def _validate_schema_coverage() -> None:
    excluded = {
        "runtimestate",
        "runtimeprobe",
        "inferencecontrol",
        "backuprecord",
        "backupschedule",
        "recoverybarrier",
        "operationalsnapshot",
    }
    active = {
        model._meta.label_lower
        for model in apps.get_app_config("runtime").get_models()
        if model._meta.model_name not in excluded
    }
    if active != set(SCHEMA):
        raise ArchiveInvalid("archive_business_schema_incomplete")


def _code_hash() -> str:
    root = Path(__file__).resolve().parents[3]
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _read_only_snapshot() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        cursor.execute("SET LOCAL statement_timeout = '300s'")
