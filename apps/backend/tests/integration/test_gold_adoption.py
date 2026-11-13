from pathlib import Path

from tests.factories.gold_driver import GoldDriver
from tests.factories.runtime import pause_worker, prepare_instance, resume_worker
from tests.integration.test_collection import command, shell
from tests.integration.test_gold_authorization import gold_driver as gold_driver


def test_gold_backup_restores_policy_qualification_and_original_receipt(
    gold_driver: GoldDriver,
    tmp_path: Path,
) -> None:
    gold_driver.action("prepare", case="BASE")
    gold_driver.action("send")
    backup = tmp_path / "backup"
    with Path(str(gold_driver.ready["private_file"])).open("a") as output:
        output.write(f"GARIMPEI_BACKUP_DIR={backup}\n")
    gold_driver.shell("""
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.operations_models import BackupRecord
from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway
from garimpei.config.env import load_operations_settings
repository=build_backup_repository();identity=repository.create(only_due=False)
record=BackupRecord.objects.get(id=identity);settings=load_operations_settings()
(settings.backup_dir/'selected').write_text(str(ArchiveGateway(settings.backup_dir).resolve(record.file_key)))
""")
    archive = (backup / "selected").read_text()
    target = prepare_instance(gold_driver.root, tmp_path, "gold_restore_" + tmp_path.name[-8:])
    command(target, "./scripts/init.sh", "--disposable")
    group = pause_worker(target)
    try:
        shell(
            target,
            f"""
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.gold_models import GoldPolicyAdoption,GoldQualification
from garimpei.infra.persistence.alert_models import AlertIntent,AlertAttempt
from garimpei.infra.persistence.operations_models import RecoveryBarrier
assert GoldPolicyAdoption.objects.get(installation='local').state=='pending'
build_backup_repository().restore({archive!r},isolated=True)
policy=GoldPolicyAdoption.objects.get(installation='local')
assert policy.state=='active' and policy.activated_at and policy.consumer_version=='gold-alert-v1'
row=AlertIntent.objects.get(state='confirmed');qualification=GoldQualification.objects.get(id=row.gold_qualification_id)
assert qualification.state=='qualified' and qualification.evidence['financial']['profit']=='800.00'
assert row.confirmed_message=='message-1' and row.confirmed_ack==1
assert AlertAttempt.objects.get(intent=row).gold_policy_verified=='gold-alert-v1'
assert RecoveryBarrier.objects.get().state=='blocked'
""",
        )
    finally:
        resume_worker(group)
        command(target, "./scripts/stop.sh", "--clean")


def test_restore_guard_rejects_policy_downgrade_before_writing(gold_driver: GoldDriver) -> None:
    gold_driver.action("prepare", case="BASE")
    gold_driver.shell("""
import json
from django.db import transaction
from garimpei.infra.gateway.operations.gold_restore import prepare_gold_restore
from garimpei.infra.gateway.operations.archive_gateway import ArchiveInvalid
from garimpei.infra.persistence.gold_models import GoldPolicyAdoption,GoldQualification
row=GoldPolicyAdoption.objects.get(installation='local');before=(row.state,row.activated_at,GoldQualification.objects.count())
raw=json.dumps({'model':'runtime.goldpolicyadoption','pk':'local','fields':{'state':'pending'}}).encode()+b'\\n'
try:
 with transaction.atomic():prepare_gold_restore({'runtime.goldpolicyadoption.jsonl':raw})
except ArchiveInvalid as error:
 assert 'archive_gold_policy_downgrade' in str(error)
else:raise AssertionError('active policy downgraded')
row.refresh_from_db();assert (row.state,row.activated_at,GoldQualification.objects.count())==before
""")
