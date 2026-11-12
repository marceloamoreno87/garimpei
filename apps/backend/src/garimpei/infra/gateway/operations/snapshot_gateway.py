"""One repeatable-read snapshot, strict schema validation, and transactional restoration."""

import hashlib
import json
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

from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.infra.gateway.operations.private_fields import (
    sanitize_transient_media,
    validate_private_fields,
)
from garimpei.infra.gateway.operations.schema import SCHEMA
from garimpei.infra.persistence.listing_models import ListingEvent


def schema_hash() -> str:
    shape = {name: fields for name, (_, fields) in SCHEMA.items()}
    return hashlib.sha256(json.dumps(shape, sort_keys=True).encode()).hexdigest()


class BusinessSnapshotGateway:
    def capture(self) -> tuple[datetime, dict[str, bytes], dict[str, int], dict[str, object]]:
        _validate_schema_coverage()
        files: dict[str, bytes] = {}
        counts: dict[str, int] = {}
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                cursor.execute("SET LOCAL statement_timeout = '300s'")
                cursor.execute("SELECT transaction_timestamp()")
                row = cursor.fetchone()
            assert row is not None
            snapshot_at = cast(datetime, row[0])
            for name, (model, fields) in SCHEMA.items():
                data, count = _capture_table(model, fields)
                files[name + ".jsonl"], counts[name] = data, count
            metadata: dict[str, object] = {
                "migrations": [
                    f"{app}.{name}"
                    for app, name in sorted(MigrationRecorder(connection).applied_migrations())
                ],
                "covered_event_cursor": ListingEvent.objects.aggregate(value=Max("sequence"))[
                    "value"
                ],
                "code_sha256": _code_hash(),
            }
        return snapshot_at, files, counts, metadata

    def validate(self, metadata: dict[str, object], files: dict[str, bytes]) -> None:
        if metadata.get("schema_hash") != schema_hash():
            raise ArchiveInvalid("archive_schema_incompatible")
        expected = {name + ".jsonl" for name in SCHEMA}
        if set(files) != expected:
            raise ArchiveInvalid("archive_tables_incomplete")
        identities = {name: _identities(name, files[name + ".jsonl"]) for name in SCHEMA}
        identities["runtime.listingevent:id"] = {
            str(row["fields"]["id"])
            for row in _records(files["runtime.listingevent.jsonl"])
            if isinstance(row["fields"], dict)
        }
        try:
            for name, data in files.items():
                _validate_table(name.removesuffix(".jsonl"), data, identities)
        except (ValidationError, ValueError, TypeError):
            raise ArchiveInvalid("archive_field_invalid") from None

    def restore(self, files: dict[str, bytes]) -> None:
        for name, data in files.items():
            _restore_table(name, data)
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
        identity = str(row["pk"])
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
    field.to_python(value)


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
