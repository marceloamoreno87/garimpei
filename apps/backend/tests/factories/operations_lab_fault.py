"""Bounded archive faults with an equivalent successful operation as control."""

import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from unittest.mock import patch
from uuid import uuid4

from django.db import connection, transaction
from django.db.models import Min

from garimpei.config.env import load_config
from garimpei.infra.gateway.operations.archive_gateway import (
    ArchiveGateway,
    ArchiveInvalid,
    copy_archive,
)
from garimpei.infra.persistence.operations_models import OperationalUnit
from garimpei.infra.repository.operations.admission import admit_enqueue
from tests.factories.monitoring import require_disposable
from tests.factories.operations_probe import delayed_origin


def measure_faults(directory: Path) -> dict[str, object]:
    """Measure five repetitions of the implemented paired eval-only faults."""
    require_disposable()
    cases = (
        "network_timeout",
        "slow_valuation",
        "slow_channel",
        "disk_full",
        "archive_interrupted",
        "export_interrupted",
        "queue_full",
    )
    rows: list[dict[str, object]] = []
    archive_root = directory / "fault-calibration-data"
    if archive_root.exists():
        raise ValueError("Fault calibration already exists; use a fresh laboratory")
    archive_root.mkdir(mode=0o700)
    for case in cases:
        for repetition in range(1, 6):
            started = time.monotonic()
            if case in {"network_timeout", "slow_valuation", "slow_channel"}:
                observation = network_fault(case)
            elif case == "queue_full":
                observation = queue_fault()
            else:
                observation = archive_fault(archive_root / case / str(repetition), case)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT count(*) FROM procrastinate_jobs WHERE status IN ('todo','doing')"
                )
                pending = int(cursor.fetchone()[0])
                cursor.execute("SELECT pg_database_size(current_database())")
                database_bytes = int(cursor.fetchone()[0])
            oldest = OperationalUnit.objects.filter(pending__gt=0).aggregate(
                oldest=Min("pending_since")
            )["oldest"]
            stored = sum(path.stat().st_size for path in archive_root.rglob("*") if path.is_file())
            rows.append(
                {
                    "case": case,
                    "repetition": repetition,
                    "seconds": time.monotonic() - started,
                    "control": observation["control"],
                    "fault": observation["fault"],
                    "disk_free_bytes": shutil.disk_usage(directory).free,
                    "sampled_archive_bytes": stored,
                    "database_bytes": database_bytes,
                    "pending_jobs_after": pending,
                    "oldest_pending_at": oldest.isoformat() if oldest else None,
                }
            )
    return {
        "measurements": rows,
        "profile_confirmed": False,
        "operational_enablement": False,
        "limits": "eval-only network deadlines; storage sampled after each repetition, not peak",
        "pending": "remaining crash points, real-load isolation and full operational profile",
    }


NAVIGATION_CASES = {
    "repeat_cursor": """
NavigationCheckpoint.objects.filter(work__cycle_id=attempt.cycle_id).update(cursor='same')
unit=nav.claim(attempt,scope,pages=True,details=False)
assert unit and unit.cursor=='same'
nav.page(attempt,unit,Page((), 'same'))
row=NavigationWork.objects.get(id=unit.turn.id)
checkpoint=NavigationCheckpoint.objects.get(work=row)
fault_detected=row.phase=='partial' and row.reason=='repeated_continuation' and checkpoint.pages==0
other=nav.claim(attempt,scope,pages=True,details=False)
assert other and other.turn.id != unit.turn.id
nav.page(attempt,other,Page((), 'next'))
control_confirmed=NavigationCheckpoint.objects.get(work_id=other.turn.id).pages==1
""",
    "lease_expired": """
unit=nav.claim(attempt,scope,pages=True,details=False)
assert unit
NavigationWork.objects.filter(id=unit.turn.id).update(generation=unit.generation+1)
fault_detected=False
try:nav.page(attempt,unit,Page((), 'next'))
except SupersededAttempt:fault_detected=True
assert not NavigationUnitReceipt.objects.exists()
other=nav.claim(attempt,scope,pages=True,details=False)
assert other
nav.page(attempt,other,Page((), 'next'))
control_confirmed=NavigationCheckpoint.objects.get(work_id=other.turn.id).pages==1
""",
    "late_result": """
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration
unit=nav.claim(attempt,scope,pages=True,details=False)
assert unit
MonitoringConfiguration.objects.filter(slot='active').update(revision=scope.revision+1)
fault_detected=False
try:nav.page(attempt,unit,Page((), 'next'))
except SupersededAttempt:fault_detected=True
assert not NavigationUnitReceipt.objects.exists()
MonitoringConfiguration.objects.filter(slot='active').update(revision=scope.revision)
other=nav.claim(attempt,scope,pages=True,details=False)
assert other
nav.page(attempt,other,Page((), 'next'))
control_confirmed=NavigationCheckpoint.objects.get(work_id=other.turn.id).pages==1
""",
    "crash_before_commit": """
unit=nav.claim(attempt,scope,pages=True,details=False)
assert unit
fault_detected=False
with patch.object(NavigationUnitReceipt.objects,'create',side_effect=RuntimeError('controlled pre-commit failure')):
 try:nav.page(attempt,unit,Page((), 'next'))
 except RuntimeError:fault_detected=True
assert NavigationCheckpoint.objects.get(work_id=unit.turn.id).pages==0
assert not NavigationUnitReceipt.objects.exists()
nav.page(attempt,unit,Page((), 'next'))
control_confirmed=NavigationCheckpoint.objects.get(work_id=unit.turn.id).pages==1 and NavigationUnitReceipt.objects.count()==1
""",
}


def navigation_script(case: str) -> str:
    """Build a transactional scenario against the real navigation repository."""
    from textwrap import indent

    setup = """import json
from django.db import transaction
from garimpei.infra.persistence.listing_models import Listing
from tests.factories.monitoring import require_disposable
require_disposable()
seed_count=Listing.objects.count()
with transaction.atomic():
"""
    bootstrap = """
from datetime import timedelta
from unittest.mock import patch
from garimpei.domain.listing.ports import Attempt, Page, SupersededAttempt
from garimpei.domain.listing.scope import Scope
from garimpei.infra.persistence.navigation_models import NavigationWork, NavigationCheckpoint, NavigationUnitReceipt
from garimpei.infra.persistence.listing_models import CollectionState
from garimpei.main import _effective_listing_settings, _listing_clock, build_navigation_repository, build_navigation_catalog, build_read_monitoring_configuration
state=CollectionState.objects.get()
cycle=state.current
cycle.finished_at=None
cycle.phase='running'
cycle.save(update_fields=['finished_at','phase'])
scope=Scope.from_snapshot(build_read_monitoring_configuration().execute())
assert scope
scope=build_navigation_catalog().decorate_scope(scope)
state.lease_until=_listing_clock(_effective_listing_settings())()+timedelta(minutes=5)
state.save(update_fields=['lease_until'])
attempt=Attempt(cycle.id,state.generation)
nav=build_navigation_repository(_effective_listing_settings())
nav.prepare(attempt,scope)
"""
    code = (
        bootstrap
        + NAVIGATION_CASES[case]
        + """
assert fault_detected and control_confirmed
transaction.set_rollback(True)
"""
    )
    tail = """
seed_preserved=Listing.objects.count()==seed_count
assert seed_preserved
print(json.dumps({'fault_detected':fault_detected,'control_confirmed':control_confirmed,'seed_preserved':seed_preserved}))
"""
    return setup + indent(code, "    ") + tail


def network_fault(case: str) -> dict[str, object]:
    """Exercise a one-second eval-only deadline against the actual loopback adapters."""
    from garimpei.domain.alert.alert import AlertPolicy, Binding, Delivery
    from garimpei.domain.listing.ports import SourceFailure
    from garimpei.domain.valuation.ports import NewSourceFailure
    from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
    from garimpei.infra.gateway.listing.fixture_source import FixtureSource
    from garimpei.infra.gateway.valuation.new_source import RetailNewSource

    require_disposable()
    binding = Binding("synthetic", "100@c.us", "200@c.us")
    delivery = Delivery(
        uuid4(), 1, binding, "Synthetic timeout control", datetime.now(UTC), None, False
    )

    def run(url: str) -> str:
        try:
            if case == "network_timeout":
                FixtureSource(url, 1)._get("/search", {})
            elif case == "slow_valuation":
                RetailNewSource(Path("unused"), url, timeout=1).offers(
                    "synthetic", datetime.now(UTC)
                )
            elif case == "slow_channel":
                outcome = WahaGateway(url, "synthetic-only", AlertPolicy(timeout=1)).send(delivery)
                return "success" if outcome.state == "confirmed" else outcome.state
            else:
                raise ValueError("Unsupported network fault")
        except (SourceFailure, NewSourceFailure):
            return "timeout"
        return "success"

    rows = []
    for delay in (0, 2):
        with delayed_origin(delay) as url:
            started = time.monotonic()
            outcome = run(url)
            rows.append({"outcome": outcome, "seconds": time.monotonic() - started})
    expected = "uncertain" if case == "slow_channel" else "timeout"
    if rows[0]["outcome"] != "success" or rows[1]["outcome"] != expected:
        raise AssertionError("Unexpected loopback timeout/control outcome")
    return {"control": rows[0], "fault": rows[1], "timeout_seconds": 1, "eval_only": True}


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
