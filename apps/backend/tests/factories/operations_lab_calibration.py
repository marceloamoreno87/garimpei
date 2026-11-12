"""Five measured copy/export/restore/reconciliation controls against owned PostgreSQL."""

import json
import tarfile
import time
from pathlib import Path
from typing import cast

from tests.factories.alert import WahaServer, serve_waha
from tests.factories.operations_evidence import serve_recovery_evidence
from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker


def _shell(instance: FoundationInstance, code: str) -> float:
    started = time.monotonic()
    result = instance.shell(code)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return time.monotonic() - started


def measure_new_stages(
    directory: Path, source: FoundationInstance, target: FoundationInstance
) -> list[dict[str, object]]:
    history = cast(
        list[dict[str, object]], json.loads((directory / "channel-messages.json").read_text())
    )
    if len(history) != 2:
        raise ValueError("Expected the two provider receipts retained during the actual fake POSTs")
    channel = WahaServer(recipient="100@g.us", messages=history)
    proof: dict[str, object] = {}
    rows: list[dict[str, object]] = []
    with serve_waha(channel) as channel_url, serve_recovery_evidence(proof) as evidence_url:
        with target.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_RECOVERY_EVIDENCE_FIXTURE_URL={evidence_url}\nGARIMPEI_ALERT_FIXTURE_URL={channel_url}\nGARIMPEI_WAHA_SESSION=synthetic\nGARIMPEI_WAHA_ACCOUNT=200@c.us\nGARIMPEI_WAHA_RECIPIENT=100@g.us\n"
            )
        for repetition in range(1, 6):
            rows.append(_repetition(directory, source, target, proof, repetition))
        if any(method == "POST" for method, _ in channel.calls):
            raise AssertionError(
                "Recovery must query the original receipts, never send another POST"
            )
    return rows


def _repetition(
    directory: Path,
    source: FoundationInstance,
    target: FoundationInstance,
    proof: dict[str, object],
    repetition: int,
) -> dict[str, object]:
    transfer = directory / f"calibration-transfer-{repetition}.json"
    create_seconds = _shell(source, f"TRANSFER={str(transfer)!r}\n" + _CAPTURE)
    data = cast(dict[str, object], json.loads(transfer.read_text()))
    selected = Path(str(data["archive"]))
    export_seconds = _shell(
        source,
        f"TRANSFER={str(transfer)!r}\n" + _EXPORT,
    )
    _scan_private_inputs(directory, source, selected)
    proof.clear()
    proof.update(cast(dict[str, object], data["proof"]))
    stopped = target.command("./scripts/stop.sh", "--clean", timeout=180)
    if stopped.returncode:
        raise RuntimeError(stopped.stdout + stopped.stderr)
    started = time.monotonic()
    ready = target.command("./scripts/init.sh", "--disposable", timeout=180)
    if ready.returncode:
        raise RuntimeError(ready.stdout + ready.stderr)
    startup_seconds = time.monotonic() - started
    group = pause_worker(target)
    try:
        restore_seconds = _shell(target, f"ARCHIVE={str(selected)!r}\n" + _RESTORE)
        verify_seconds = _shell(target, f"IDENTITY={str(data['id'])!r}\n" + _VERIFY)
        with target.database() as database:
            value = database.execute("SELECT pg_database_size(current_database())").fetchone()
            target_bytes = int(str(value[0])) if value else 0
    finally:
        resume_worker(group)
        stopped = target.command("./scripts/stop.sh", "--clean", timeout=180)
        if stopped.returncode:
            raise RuntimeError(stopped.stdout + stopped.stderr)
    return {
        "repetition": repetition,
        "case": "control",
        "corpus": "12 identities, versioned facts, two original loopback receipts",
        "backup_seconds_including_cli": create_seconds,
        "export_seconds_including_cli": export_seconds,
        "restore_seconds_including_cli": restore_seconds,
        "verify_seconds_including_cli": verify_seconds,
        "destination_startup_seconds": startup_seconds,
        "archive_bytes": data["bytes"],
        "protected_originals": data["protected_originals"],
        "source_database_bytes": data["database_bytes"],
        "destination_database_bytes": target_bytes,
        "restoration_state": "verified",
        "duplicate_posts": 0,
        "private_input_scan": "passed",
    }


def _scan_private_inputs(directory: Path, source: FoundationInstance, selected: Path) -> None:
    canaries = list(json.loads((directory / "canaries.json").read_text()).values())
    for line in source.private_file.read_text().splitlines():
        name, _, value = line.partition("=")
        if name in {"DJANGO_SECRET_KEY", "POSTGRES_PASSWORD", "WAHA_API_KEY"}:
            canaries.append(value)
    with tarfile.open(selected, "r:gz") as archive:
        for member in archive:
            stream = archive.extractfile(member)
            if stream is None:
                raise AssertionError("Unexpected archive entry")
            data = stream.read()
            if any(str(canary).encode() in data for canary in canaries):
                raise AssertionError("Private input unexpectedly copied")


_CAPTURE = """
import json
from pathlib import Path
from django.db import connection
from garimpei.config.env import load_config,load_operations_settings
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.alert_models import AlertIntent
from garimpei.infra.persistence.operations_models import BackupRecord
r=build_backup_repository();identity=r.create();record=BackupRecord.objects.get(id=identity)
metadata,files=r._archives.read(r._archives.resolve(record.file_key))
assert len(metadata['protected_media'])==1 and all('thumbnail' in item for item in metadata['protected_media'])
from garimpei.infra.persistence.media_models import MediaReference
assert not MediaReference.objects.filter(consumer='backup',released_at=None).exists()
entries=[]
for row in AlertIntent.objects.all():
 attempt=row.attempts.order_by('-ordinal').first()
 entries.append({'id':str(row.id),'state':row.state,'body':row.body,'session':row.session,'recipient':row.recipient,'account':row.account,'attempt_id':str(attempt.id) if attempt else None,'message_id':row.confirmed_message})
proof={'format_version':1,'complete':True,'source_installation':load_config().environment_id,'backup_id':str(identity),'snapshot_at':record.snapshot_at.isoformat(),'intents':entries}
with connection.cursor() as cursor:
 cursor.execute('SELECT pg_database_size(current_database())');database_bytes=cursor.fetchone()[0]
value={'id':str(identity),'archive':str(load_operations_settings().backup_dir/record.file_key),'bytes':record.size,'database_bytes':database_bytes,'proof':proof,'protected_originals':len(metadata['protected_media'])}
p=Path(TRANSFER);p.write_text(json.dumps(value));p.chmod(0o600)
"""

_EXPORT = """
import json
from pathlib import Path
from uuid import UUID,uuid4
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.operations_models import BackupRecord
value=json.loads(Path(TRANSFER).read_text());r=build_backup_repository()
identity=r.export(UUID(value['id']),uuid4());copy=BackupRecord.objects.get(id=identity);source=BackupRecord.objects.get(id=value['id'])
assert copy.sha256==source.sha256 and r._archives.resolve(copy.file_key).read_bytes()==r._archives.resolve(source.file_key).read_bytes()
assert r.verify(source.id)['restoration_state']=='not_tested'
"""

_RESTORE = """
from garimpei.main import build_backup_repository,build_recovery_guard
from garimpei.infra.persistence.listing_models import Listing,ManualCondition
from garimpei.infra.persistence.operations_models import OperationalUnit
r=build_backup_repository();r.restore(ARCHIVE,isolated=True)
assert Listing.objects.count()==12 and build_recovery_guard()()
assert ManualCondition.objects.count()==1
import hashlib
from garimpei.main import build_media_store
from garimpei.infra.persistence.media_models import MediaAsset
from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
asset=MediaAsset.objects.get(state='available',thumbnail_state='ready');queries=PostgresMediaQueries()
assert hashlib.sha256(build_media_store().read(queries.file(asset.listing_id,asset.id,'original'))).hexdigest()==asset.sha256
assert hashlib.sha256(build_media_store().read(queries.file(asset.listing_id,asset.id,'miniatura'))).hexdigest()==asset.thumbnail_hash
unit=OperationalUnit.objects.get(scope='controlled-recovery')
assert unit.checkpoint=='confirmed-A' and unit.failures==2 and unit.suspended
"""

_VERIFY = """
from uuid import UUID
from garimpei.main import build_backup_repository,build_recovery_guard
result=build_backup_repository().verify(UUID(IDENTITY))
assert result['restoration_state']=='verified' and not build_recovery_guard()()
"""
