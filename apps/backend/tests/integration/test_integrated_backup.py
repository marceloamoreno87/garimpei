"""Cross-feature recovery preserves assessment history and its alert provenance."""

from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, prepare_instance, resume_worker
from tests.integration.test_collection import command, shell


def test_backup_restores_assessment_and_alert_provenance(tmp_path: Path) -> None:
    source_private = tmp_path / "source"
    source_private.mkdir()
    with first_eligibility_scenario(source_private) as (source, _, _, _):
        backup_dir = tmp_path / "backups"
        with source.private_file.open("a") as output:
            output.write(f"GARIMPEI_BACKUP_DIR={backup_dir}\n")
        source_group = pause_worker(source)
        target = prepare_instance(
            source.root, tmp_path, "union_restore_" + source.config.instance[-8:]
        )
        command(target, "./scripts/init.sh", "--disposable")
        target_group = pause_worker(target)
        try:
            shell(
                source,
                """
from uuid import uuid4
from django.utils.timezone import now
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.listing_models import Listing,ListingEvent
from garimpei.infra.persistence.assessment_models import ConditionAssessment,AssessmentHead
from garimpei.infra.persistence.alert_models import AlertEventDecision,FirstAlertIdentity,FirstEligibilityDecision
from garimpei.infra.persistence.operations_models import BackupRecord
from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway
from garimpei.config.env import load_operations_settings
listing=Listing.objects.select_related('latest').get(external_id='16001')
assessment=ConditionAssessment.objects.create(id=uuid4(),listing=listing,observation=listing.latest,
 input_fingerprint='a'*64,policy_version='recovery-policy',prompt_version='recovery-prompt',
 schema_version='recovery-schema',model_revision='recovery-model',input_snapshot={'text':'controlled'},
 generation=3,status='complete',condition='uncertain',sufficient=False,reason='controlled_history',
 result={'coverage':'controlled'},created_at=now(),updated_at=now(),analyzed_at=now(),publication_order=3)
AssessmentHead.objects.create(listing=listing,observation=listing.latest,input_fingerprint='a'*64,
 generation=3,current=assessment,confirmed=assessment,updated_at=now())
event=ListingEvent.objects.filter(listing=listing).first()
assert event is not None
AlertEventDecision.objects.update_or_create(event=event,defaults={'next_action':now(),
 'assessment_id':assessment.id,'assessment_revision':3})
identity,_=FirstAlertIdentity.objects.get_or_create(installation='local',listing=listing,
 defaults={'next_action':now()})
FirstEligibilityDecision.objects.create(identity=identity,generation=999,signature='b'*64,
 observation=listing.latest,state='excluded',reason='controlled_recovery',publication_status='unknown',
 evaluated_at=now(),assessment_id=assessment.id,assessment_revision=3)
repository=build_backup_repository();identity=repository.create(only_due=False)
record=BackupRecord.objects.get(id=identity);settings=load_operations_settings()
gateway=ArchiveGateway(settings.backup_dir)
(settings.backup_dir/'selected').write_text(str(gateway.resolve(record.file_key)))
(settings.backup_dir/'assessment').write_text(str(assessment.id))
""",
            )
            archive = (backup_dir / "selected").read_text()
            assessment = (backup_dir / "assessment").read_text()
            shell(
                target,
                f"""
from garimpei.main import build_backup_repository
from garimpei.infra.persistence.assessment_models import ConditionAssessment,AssessmentHead
from garimpei.infra.persistence.alert_models import AlertEventDecision,FirstEligibilityDecision
build_backup_repository().restore({archive!r},isolated=True)
assessment=ConditionAssessment.objects.get(id={assessment!r})
assert assessment.input_snapshot=={{'text':'controlled'}} and assessment.generation==3
head=AssessmentHead.objects.get(listing=assessment.listing)
assert head.current_id==assessment.id and head.confirmed_id==assessment.id
assert AlertEventDecision.objects.filter(assessment_id=assessment.id,assessment_revision=3).exists()
assert FirstEligibilityDecision.objects.filter(assessment_id=assessment.id,assessment_revision=3).exists()
""",
            )
        finally:
            resume_worker(target_group)
            command(target, "./scripts/stop.sh", "--clean")
            resume_worker(source_group)
