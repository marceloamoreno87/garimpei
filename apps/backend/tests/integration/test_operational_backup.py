"""Private snapshot/export/restore against real, independently owned PostgreSQL instances."""

from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, prepare_instance, resume_worker
from tests.integration.test_collection import command, shell


def test_snapshot_export_and_isolated_restore_keep_identity_and_dispatch_barrier(
    tmp_path: Path,
) -> None:
    source_private = tmp_path / "source"
    source_private.mkdir()
    with first_eligibility_scenario(source_private) as (source, _, _, _):
        with source.private_file.open("a") as output:
            output.write(f"GARIMPEI_BACKUP_DIR={tmp_path / 'source-backups'}\n")
        group = pause_worker(source)
        target = prepare_instance(
            source.root, tmp_path, "f17_restore_" + source.config.instance[-8:]
        )
        with target.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_BACKUP_DIR={tmp_path / 'target-backups'}\nGARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERTS_ENABLED=false\n"
            )
        command(target, "./scripts/init.sh", "--disposable")
        target_group = pause_worker(target)
        try:
            shell(
                source,
                """
from uuid import uuid4
from pathlib import Path
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.operations_models import BackupRecord
from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway
from garimpei.config.env import load_operations_settings
l=Listing.objects.select_related('latest').get(external_id='16001')
e=dict(l.latest.evidence); e['image_url']='https://scontent.example.test/photo.jpg?oh=synthetic-media-canary'
l.latest.evidence=e; l.latest.save()
r=build_backup_repository(); identity=r.create(only_due=True)
assert identity is not None and r.create(only_due=True) is None
record=BackupRecord.objects.get(id=identity); settings=load_operations_settings()
gateway=ArchiveGateway(settings.backup_dir)
metadata,files=gateway.read(gateway.resolve(record.file_key))
assert b'synthetic-media-canary' not in b''.join(files.values())
assert str(l.latest_id).encode() in files['runtime.listingobservation.jsonl']
assert metadata['schema_hash'] and metadata['migrations'] and metadata['code_sha256']
request=uuid4(); exported=r.export(identity,request)
assert r.export(identity,request)==exported
copy=BackupRecord.objects.get(id=exported)
assert copy.sha256==record.sha256 and gateway.resolve(copy.file_key).read_bytes()==gateway.resolve(record.file_key).read_bytes()
assert r.verify(identity)['restoration_state']=='not_tested'
(settings.backup_dir/'selected').write_text(str(gateway.resolve(record.file_key)))
(settings.backup_dir/'expected-id').write_text(str(l.id))
""",
            )
            selected = (tmp_path / "source-backups/selected").read_text()
            expected = (tmp_path / "source-backups/expected-id").read_text()
            shell(
                target,
                f"""
from garimpei.main import build_backup_repository,build_recovery_guard,build_operational_status,build_alert_store
from garimpei.domain.alert.alert import Binding
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import AlertFeedCursor
from garimpei.infra.persistence.operations_models import RecoveryBarrier
from garimpei.domain.operations.errors import OperationsError
from garimpei.config.env import load_operations_settings
from django.utils import timezone
r=build_backup_repository(); r.restore({selected!r},isolated=True)
assert Listing.objects.get(external_id='16001').id==__import__('uuid').UUID({expected!r})
assert AlertFeedCursor.objects.get().dispatch_suspended
assert build_recovery_guard()() and RecoveryBarrier.objects.get().state=='blocked'
assert load_operations_settings().recovery_file.exists()
assert build_operational_status().execute()['dispatch_suspended']
try:r.restore({selected!r},isolated=True)
except OperationsError as e:assert e.code=='restore_requires_empty_disposable_eval'
else:raise AssertionError('nonempty destination accepted')
""",
            )
        finally:
            resume_worker(target_group)
            command(target, "./scripts/stop.sh", "--clean")
            resume_worker(group)
