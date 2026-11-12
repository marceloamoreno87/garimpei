"""Admission can stop new work, while already authorized receipt writes bypass this gate."""

import hashlib
import shutil
from pathlib import Path
from uuid import uuid4

from django.db import connection
from django.utils import timezone

from garimpei.domain.operations.admission import Admission
from garimpei.infra.persistence.operations_models import OperationalUnit


def admit_enqueue(queue: str, installation: str, directory: Path) -> bool:
    if queue == "runtime":
        return True
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", ["operations." + queue]
        )
        cursor.execute(
            "SELECT count(*) FROM procrastinate_jobs WHERE queue_name=%s AND status IN ('todo','doing')",
            [queue],
        )
        row = cursor.fetchone()
    pending = int(str(row[0])) if row else 0
    decision = _capacity(pending, directory)
    _pressure(queue, installation, decision.reason, pending)
    return decision.reason is None


def transmission_capacity(directory: Path) -> bool:
    return _capacity(0, directory).reason is None


def _capacity(pending: int, directory: Path) -> Admission:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_database_size(current_database())")
        row = cursor.fetchone()
        cursor.execute("SELECT to_regclass('runtime_mediaasset')")
        media = cursor.fetchone()
    database_bytes = int(str(row[0])) if row else 0
    media_bytes = _media_bytes() if media and media[0] else 0
    return Admission(pending, database_bytes + media_bytes, shutil.disk_usage(directory).free)


def _media_bytes() -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT coalesce(sum(byte_count+thumbnail_bytes),0) FROM runtime_mediaasset WHERE state IN ('available','removing')"
        )
        row = cursor.fetchone()
    return int(str(row[0])) if row else 0


def _pressure(queue: str, installation: str, reason: str | None, pending: int) -> None:
    key = hashlib.sha256(("queue:" + queue).encode()).hexdigest()
    if reason is None:
        OperationalUnit.objects.filter(
            installation=installation, stage=queue, key=key, revision=0
        ).update(pending=0, suspended=False, reason="capacity_available")
        return
    row, _ = OperationalUnit.objects.get_or_create(
        installation=installation,
        stage=queue,
        key=key,
        revision=0,
        defaults={"id": uuid4(), "scope": queue, "pending_since": timezone.now()},
    )
    row.pending, row.suspended, row.reason = max(1, pending), True, reason
    row.save(update_fields=["pending", "suspended", "reason"])
