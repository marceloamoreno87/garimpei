from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import shell
from tests.integration.test_operational_recovery import operational_instance as operational_instance


def test_restart_recovers_interrupted_archives_and_schedule(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from django.utils.timezone import now
from garimpei.config.env import load_config
from garimpei.domain.operations.errors import OperationsError
from garimpei.infra.persistence.operations_models import BackupRecord,BackupSchedule
from garimpei.main import build_backup_repository
r=build_backup_repository();original=r.create();assert original
prior=BackupRecord.objects.get(id=original);prior_bytes=r._archives.resolve(prior.file_key).read_bytes()
schedule=BackupSchedule.objects.get(installation=load_config().environment_id)
next_due=schedule.next_due_at
assert r.create(only_due=True) is None
schedule.refresh_from_db();assert schedule.next_due_at==next_due
# Simulate process death after durable file publication but before catalog commit.
orphan=uuid4();record=BackupRecord.objects.create(id=orphan,installation=load_config().environment_id,kind='backup',started_at=now()-timedelta(minutes=10))
path=r._archives.write('completed',str(orphan),{'format_version':1},{'records.jsonl':b'{}\\n'})
partial=r._archives.root/'partial'/(str(orphan)+'.tar.gz');partial.write_bytes(b'interrupted')
r.prune();record.refresh_from_db()
assert record.state=='failed' and record.reason=='operation_interrupted'
assert not path.exists() and not partial.exists()
assert r._archives.resolve(prior.file_key).read_bytes()==prior_bytes
schedule.refresh_from_db();assert schedule.failures==1 and schedule.next_due_at==next_due
# An interrupted export never publishes success and leaves its local source intact.
with patch('garimpei.infra.repository.operations.backup_repository.copy_archive',side_effect=OSError('controlled write interruption')):
 try:r.export(original,uuid4())
 except OperationsError as error:assert error.code=='export_failed'
 else:raise AssertionError('interrupted export succeeded')
assert BackupRecord.objects.filter(kind='export',state='failed').exists()
assert r._archives.resolve(prior.file_key).read_bytes()==prior_bytes
""",
    )


def test_retention_preserves_active_exports_and_protected_diagnostics(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from datetime import timedelta
from uuid import uuid4
from django.utils.timezone import now
from garimpei.config.env import load_config
from garimpei.infra.persistence.operations_models import BackupRecord,OperationalDiagnostic,OperationalSnapshot
from garimpei.infra.repository.operations.progress_repository import PostgresOperationalRepository
from garimpei.main import build_backup_repository
r=build_backup_repository();identity=load_config().environment_id
first=r.create();assert first
source=BackupRecord.objects.get(id=first)
export=r.export(first,uuid4());row=BackupRecord.objects.get(id=export)
BackupRecord.objects.filter(id=export).update(finished_at=now()-timedelta(days=2),transferring=1)
BackupRecord.objects.filter(id=first).update(transferring=1)
for _ in range(8):assert r.create()
source.refresh_from_db();assert source.state=='completed' and r._archives.resolve(source.file_key).exists()
r.prune();row.refresh_from_db();assert row.state=='completed' and r._archives.resolve(row.file_key).exists()
BackupRecord.objects.filter(id__in=[first,export]).update(transferring=0)
store=PostgresOperationalRepository(identity,now)
store.failure('listing','retention-protected',1,'source_transport',now()-timedelta(days=8))
diagnostic=OperationalDiagnostic.objects.filter(unit__scope='retention-protected').get()
diagnostic.protected=True;diagnostic.save()
store.failure('listing','retention-disposable',1,'source_transport',now()-timedelta(days=8))
snapshot=uuid4();OperationalSnapshot.objects.create(id=snapshot,installation=identity,created_at=now()-timedelta(days=8),payload={})
result=r.prune();assert result['expired_exports']==1 and result['diagnostics']>=1 and result['snapshots']>=1
row.refresh_from_db();source.refresh_from_db()
assert row.state=='removed' and source.state=='removed'
assert BackupRecord.objects.filter(installation=identity,kind='backup',state='completed').count()==7
assert not r._archives.resolve(row.file_key).exists()
assert OperationalDiagnostic.objects.filter(id=diagnostic.id,protected=True).exists()
assert not OperationalSnapshot.objects.filter(id=snapshot).exists()
""",
    )


def test_backup_budget_is_visible_and_explicit_resume_restarts_due_schedule(
    operational_instance: FoundationInstance,
) -> None:
    with operational_instance.private_file.open("a") as output:
        output.write("GARIMPEI_OPERATIONS_ENABLED=true\n")
    shell(
        operational_instance,
        """
from unittest.mock import patch
from django.utils.timezone import now
from garimpei.config.env import load_config
from garimpei.domain.operations.errors import OperationsError
from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.infra.persistence.operations_models import OperationalUnit,BackupSchedule
from garimpei.infra.repository.operations.progress_repository import PostgresOperationalRepository
from garimpei.main import build_backup_repository
r=build_backup_repository();identity=load_config().environment_id
with patch.object(r._archives,'write',side_effect=ArchiveInvalid('controlled disk limit')):
 for _ in range(3):
  try:r.create()
  except OperationsError as error:assert error.code=='backup_creation_failed'
  else:raise AssertionError('disk limit published success')
row=OperationalUnit.objects.get(installation=identity,scope='automatic-backup')
assert row.suspended and row.failures==3
assert r.create(only_due=True) is None
checkpoint=row.checkpoint
PostgresOperationalRepository(identity,now).resume(row.id,'maintenance',1)
row.refresh_from_db();schedule=BackupSchedule.objects.get(installation=identity)
assert row.checkpoint==checkpoint and row.failures==0 and schedule.failures==0
assert r.create(only_due=True)
row.refresh_from_db();assert not row.suspended and row.last_progress_at and row.pending==0
""",
    )
