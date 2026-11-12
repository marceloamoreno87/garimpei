"""Cross-feature recovery preserves assessment, identity, research, and alert provenance."""

from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, prepare_instance, resume_worker
from tests.integration.test_collection import command, shell


def test_backup_restores_assessment_identity_research_and_alert_provenance(tmp_path: Path) -> None:
    source_private = tmp_path / "source"
    source_private.mkdir()
    with first_eligibility_scenario(source_private, target_title="PlayStation 5 Slim disco") as (
        source,
        _,
        _,
        _,
    ):
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
from garimpei.infra.persistence.identity_models import ManualIdentityRevision,ProductIdentification,IdentityProgress
from garimpei.infra.persistence.research_models import ComparableInvestigation,InvestigationTarget,ResearchQuery,ResearchCandidateDecision
from garimpei.infra.repository.valuation.identity_mapper import identify_row,encode_identity
from garimpei.infra.repository.valuation.research_mapper import policy_snapshot
from tests.factories.comparable_research import controlled_limits
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
manual=ManualIdentityRevision.objects.create(listing=listing,revision=999,observation=listing.latest,
 action='save',values={'family':'playstation5','model':'ps5','generation':'slim','edition':'disc','capacity':'1tb'},
 reviewed_conflicts=[],recorded_at=now())
progress,_=IdentityProgress.objects.update_or_create(listing=listing,
 defaults={'manual_revision':999,'manual':manual,'current':None})
identified=identify_row(listing,progress)
assert identified.state=='identified' and identified.product_key is not None
identification=ProductIdentification.objects.create(listing=listing,observation=listing.latest,
 manual_revision=999,policy=identified.policy_version,state=identified.state,
 product_key=identified.product_key,result=encode_identity(identified),recorded_at=now())
progress.current=identification;progress.save(update_fields=['current'])
investigation=ComparableInvestigation.objects.create(signature='c'*64,product_key=identified.product_key,
 configuration_id=listing.latest.cycle.state.configuration_id,
 configuration_revision=listing.latest.cycle.revision,origin_interest='controlled recovery',
 scope_key=listing.latest.cycle.scope_key,context={'source':'controlled','verified':True},
 limits=policy_snapshot(controlled_limits()),term='PlayStation 5 Slim disco 1TB',policy='recovery-research-v1',
 state='exhausted',reason='source_exhausted',pages=1,details=1,attempts=1,
 generation=999,last_turn=999,requested_at=now(),last_progress_at=now(),cycle=listing.latest.cycle)
target=InvestigationTarget.objects.create(investigation=investigation,listing=listing,
 observation=listing.latest,manual_revision=999,configuration_revision=investigation.configuration_revision)
query=ResearchQuery.objects.create(investigation=investigation,ordinal=999,term=investigation.term,
 requested={'purpose':'research','product_key':identified.product_key},
 observed={'context_verified':True,'source':'controlled'},state='complete',reason='source_exhausted',
 requested_at=investigation.requested_at,confirmed_at=now())
ResearchCandidateDecision.objects.create(query=query,target=target,observation=listing.latest,
 policy='recovery-research-v1',decision='excluded',reasons=['self'],
 evidence={'external_id':listing.external_id,'price_kind':'announced','product_key':identified.product_key},
 recorded_at=now())
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
from garimpei.infra.persistence.identity_models import ManualIdentityRevision,ProductIdentification,IdentityProgress
from garimpei.infra.persistence.research_models import ComparableInvestigation,InvestigationTarget,ResearchQuery,ResearchCandidateDecision
from garimpei.infra.repository.valuation.identity_mapper import decode_identity
build_backup_repository().restore({archive!r},isolated=True)
assessment=ConditionAssessment.objects.get(id={assessment!r})
assert assessment.input_snapshot=={{'text':'controlled'}} and assessment.generation==3
head=AssessmentHead.objects.get(listing=assessment.listing)
assert head.current_id==assessment.id and head.confirmed_id==assessment.id
assert AlertEventDecision.objects.filter(assessment_id=assessment.id,assessment_revision=3).exists()
assert FirstEligibilityDecision.objects.filter(assessment_id=assessment.id,assessment_revision=3).exists()
manual=ManualIdentityRevision.objects.get(listing=assessment.listing,revision=999)
assert manual.observation_id==assessment.observation_id and manual.action=='save'
assert manual.values=={{'family':'playstation5','model':'ps5','generation':'slim','edition':'disc','capacity':'1tb'}}
assert manual.reviewed_conflicts==[] and manual.previous_id is None
identification=ProductIdentification.objects.get(listing=assessment.listing,manual_revision=999)
assert identification.observation_id==manual.observation_id and identification.state=='identified'
identified=decode_identity(identification.result)
assert identified.observation_id==manual.observation_id and identified.manual_revision==999
assert identified.product_key==identification.product_key and identified.policy_version==identification.policy
capacity=next(attribute for attribute in identified.attributes if attribute.name=='capacity')
assert capacity.origin=='manual' and capacity.value=='1tb' and capacity.observation_id==manual.observation_id
assert capacity.recorded_at==manual.recorded_at,(capacity.recorded_at,manual.recorded_at)
progress=IdentityProgress.objects.get(listing=assessment.listing)
assert progress.manual_revision==999 and progress.manual_id==manual.id and progress.current_id==identification.id
investigation=ComparableInvestigation.objects.get(signature='c'*64)
assert investigation.product_key==identification.product_key and investigation.state=='exhausted'
assert investigation.reason=='source_exhausted' and investigation.generation==999
assert investigation.cycle_id==assessment.observation.cycle_id
assert investigation.configuration_id==assessment.observation.cycle.state.configuration_id
assert investigation.configuration_revision==assessment.observation.cycle.revision
assert investigation.context=={{'source':'controlled','verified':True}}
assert investigation.limits['policy_version']=='controlled-only-v1'
target=InvestigationTarget.objects.get(investigation=investigation,manual_revision=999)
assert target.listing_id==assessment.listing_id and target.observation_id==manual.observation_id
assert target.configuration_revision==investigation.configuration_revision and target.active
query=ResearchQuery.objects.get(investigation=investigation,ordinal=999)
assert query.state=='complete' and query.reason=='source_exhausted' and query.term==investigation.term
assert query.requested=={{'purpose':'research','product_key':identification.product_key}}
assert query.observed=={{'context_verified':True,'source':'controlled'}}
assert query.requested_at==investigation.requested_at and query.confirmed_at>=query.requested_at
decision=ResearchCandidateDecision.objects.get(query=query,target=target)
assert decision.observation_id==manual.observation_id and decision.policy=='recovery-research-v1'
assert decision.decision=='excluded' and decision.reasons==['self']
assert decision.evidence=={{'external_id':'16001','price_kind':'announced','product_key':identification.product_key}}
""",
            )
        finally:
            resume_worker(target_group)
            command(target, "./scripts/stop.sh", "--clean")
            resume_worker(source_group)
