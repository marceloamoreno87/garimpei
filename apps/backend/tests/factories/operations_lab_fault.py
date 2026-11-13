"""Bounded archive faults with an equivalent successful operation as control."""

import json
import time
from pathlib import Path
from typing import BinaryIO
from unittest.mock import patch
from uuid import uuid4

from django.db import connection, transaction

from garimpei.config.env import load_config
from garimpei.infra.gateway.operations.archive_gateway import (
    ArchiveGateway,
    ArchiveInvalid,
    copy_archive,
)
from garimpei.infra.persistence.operations_models import OperationalUnit
from garimpei.infra.repository.operations.admission import admit_enqueue
from tests.factories.monitoring import require_disposable


def queue_fault() -> dict[str, object]:
    require_disposable()
    config = load_config()
    marker = str(uuid4())
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM procrastinate_jobs WHERE queue_name IN ('valuation','media') "
                "AND status IN ('todo','doing')"
            )
            if cursor.fetchone()[0]:
                raise ValueError("Queue fault requires empty owned test queues")
            for queue, count in (("valuation", 1000), ("media", 999)):
                cursor.execute(
                    "INSERT INTO procrastinate_jobs(task_name,args,queue_name,status) "
                    "SELECT 'garimpei.evaluate_valuation',%s::jsonb,%s,'todo' "
                    "FROM generate_series(1,%s)",
                    [json.dumps({"fault_marker": marker}), queue, count],
                )
        started = time.monotonic()
        control = admit_enqueue("media", config.environment_id, config.directory)
        control_seconds = time.monotonic() - started
        started = time.monotonic()
        admitted = admit_enqueue("valuation", config.environment_id, config.directory)
        fault_seconds = time.monotonic() - started
        unit = OperationalUnit.objects.get(
            installation=config.environment_id, stage="valuation", scope="valuation", revision=0
        )
        if admitted or not control or not unit.suspended or unit.reason != "queue_full":
            raise AssertionError("Queue capacity did not produce the expected isolation")
        pending = unit.pending
        transaction.set_rollback(True)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT count(*) FROM procrastinate_jobs WHERE args->>'fault_marker'=%s", [marker]
        )
        cleaned = cursor.fetchone()[0] == 0
    if not cleaned:
        raise AssertionError("Queue fault left synthetic jobs behind")
    return {
        "control": {"admitted": control, "pending": 999, "seconds": control_seconds},
        "fault": {"admitted": admitted, "pending": pending, "seconds": fault_seconds},
        "cleaned": cleaned,
    }


def archive_fault(directory: Path, case: str) -> dict[str, object]:
    require_disposable()
    gateway = ArchiveGateway(directory, reserve_bytes=0, budget_bytes=1024 * 1024)
    metadata: dict[str, object] = {"format_version": 1}
    payload = {"records.jsonl": b'{"synthetic":true}\n'}
    started = time.monotonic()
    prior = gateway.write("completed", str(uuid4()), metadata, payload)
    if case == "export_interrupted":
        started = time.monotonic()
        copy_archive(gateway, prior, str(uuid4()))
    control_seconds = time.monotonic() - started
    before = prior.read_bytes()
    identity = str(uuid4())

    def interrupt_write(output: BinaryIO, *_args: object) -> None:
        output.write(b"partial")
        raise OSError("controlled archive interruption")

    def interrupt_copy(reader: BinaryIO, output: BinaryIO, *_args: object) -> None:
        output.write(reader.read(8))
        raise OSError("controlled export interruption")

    started = time.monotonic()
    rejected = False
    try:
        if case == "disk_full":
            limited = ArchiveGateway(directory, reserve_bytes=0, budget_bytes=1)
            limited.write("completed", identity, metadata, payload)
        elif case == "archive_interrupted":
            with patch.object(gateway, "_write_tar", side_effect=interrupt_write):
                gateway.write("completed", identity, metadata, payload)
        elif case == "export_interrupted":
            with patch(
                "garimpei.infra.gateway.operations.archive_gateway._copy_bytes",
                side_effect=interrupt_copy,
            ):
                copy_archive(gateway, prior, identity)
        else:
            raise ValueError("Unsupported archive fault")
    except (ArchiveInvalid, OSError):
        rejected = True
    previous_preserved = prior.read_bytes() == before
    no_partial = (
        not (directory / "partial" / f"{identity}.tar.gz").exists()
        and not (directory / "completed" / f"{identity}.tar.gz").exists()
        and not (directory / "exports" / f"{identity}.tar.gz").exists()
    )
    if not rejected or not previous_preserved or not no_partial:
        raise AssertionError("Archive fault failed to preserve the completed control")
    return {
        "control": {"completed": True, "seconds": control_seconds},
        "fault": {
            "rejected": rejected,
            "previous_preserved": previous_preserved,
            "no_partial": no_partial,
            "seconds": time.monotonic() - started,
        },
    }
