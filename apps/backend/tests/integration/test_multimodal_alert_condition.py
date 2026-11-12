from pathlib import Path

import pytest

from tests.factories.assessment_origin import serve_assessment_images
from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import command, shell
from tests.integration.test_first_eligibility import target_messages, wait_first


@pytest.mark.parametrize("finding", ["light_wear", "clear_defect"])
def test_first_alert_waits_for_complete_photo_evidence_and_keeps_its_confirmed_receipt(
    tmp_path: Path,
    finding: str,
) -> None:
    with (
        serve_assessment_images() as (origin, _requests),
        first_eligibility_scenario(tmp_path) as (instance, source, clock, channel),
    ):
        group = pause_worker(instance)
        try:
            with instance.private_file.open("a") as output:
                output.write(
                    f"GARIMPEI_ASSESSMENT_ENABLED=true\nGARIMPEI_MEDIA_ROOT={tmp_path}/media\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_MEDIA_MIN_FREE_BYTES=1048576\nGARIMPEI_MEDIA_EVAL_ORIGIN={origin}\n"
                )
            source.rows["16001"]["description"] = "O aparelho funciona perfeitamente."
            clock.advance(61)
            shell(
                instance,
                """from garimpei.main import reconcile_listings,build_listing_task_handler,build_read_condition,build_classify_condition,build_first_alert_store,build_read_profit,build_alert_handler,_listing_clock
from garimpei.config.env import load_listing_settings
from garimpei.infra.persistence.listing_models import CollectionState,Listing
from garimpei.infra.persistence.alert_models import AlertIntent,AlertAttempt,FirstAlertIdentity
clock=_listing_clock(load_listing_settings())
CollectionState.objects.update(next_attempt_at=clock())
for _ in range(40):
 reconcile_listings();state=CollectionState.objects.filter(current_id__isnull=False).first()
 if state is None:break
 build_listing_task_handler().execute(str(state.current_id),state.generation)
l=Listing.objects.get(external_id='16001');condition=build_read_condition().execute(l.id).state
assert condition.analysis.condition=='uncertain' and not condition.satisfies_alert_condition
store=build_first_alert_store();store.adopt(clock());store.publish(l.id,store.prepare(l.id),build_read_profit().execute(l.id),clock())
assert FirstAlertIdentity.objects.get(listing=l).reason=='waiting_condition_assessment'
build_classify_condition().execute(l.id,'good',condition.revision)
assert build_read_condition().execute(l.id).state.effective=='good'
assert not build_read_condition().execute(l.id).state.satisfies_alert_condition
for stage in ('adopt','refresh','reconcile','send'):build_alert_handler(stage).execute()
assert not AlertIntent.objects.filter(first_decision__identity__listing=l).exists()
assert not AlertAttempt.objects.exists()
""",
            )
            assert not target_messages(channel)
            source.rows["16001"]["media"] = dict(
                presence="present",
                complete=True,
                reason="",
                photos=[
                    dict(
                        key="alert-photo-" + str(index),
                        primary=index == 0,
                        correlated=True,
                        variants=[dict(url=origin + "/" + filename, width=640, height=480)],
                    )
                    for index, filename in enumerate(
                        ("console-light_wear.png", "console-suspected.png")
                    )
                ],
            )
            clock.advance(61)
            shell(
                instance,
                """from garimpei.main import reconcile_listings,build_listing_task_handler,build_read_condition,build_media_repository,build_media_runner,_listing_clock
from garimpei.config.env import load_listing_settings
from garimpei.infra.persistence.listing_models import CollectionState,Listing
from garimpei.infra.persistence.assessment_models import ConditionAssessment
from django.utils.timezone import now
from tests.factories.assessment import assessment_context
clock=_listing_clock(load_listing_settings());CollectionState.objects.update(next_attempt_at=clock())
for _ in range(40):
 reconcile_listings();state=CollectionState.objects.filter(current_id__isnull=False).first()
 if state is None:break
 build_listing_task_handler().execute(str(state.current_id),state.generation)
for _ in range(8):
 for job in build_media_repository().due(now()):build_media_runner().execute(job)
l=Listing.objects.get(external_id='16001');context=assessment_context();context.gateway.kind=FINDING_KIND;work=context.prepare.execute(l.id)
assert not build_read_condition().execute(l.id).state.satisfies_alert_condition
for _ in range(6):context.run.execute()
assert context.complete.execute(work.id)
state=build_read_condition().execute(l.id).state
assert state.assessment.sufficient and state.satisfies_alert_condition and state.manual=='good'
assert state.assessment.runtime=='controlled_fake'
""".replace("FINDING_KIND", repr(finding)),
            )
        finally:
            resume_worker(group)
        wait_first(channel, clock)
        assert len(target_messages(channel)) == 1
        body = str(target_messages(channel)[0]["body"])
        assert "Condição provável:" in body and "funcionamento declarado pelo vendedor" in body
        assert "Sinal visual do controle sintético" in body
        if finding == "clear_defect":
            assert "Escolha manual" in body and "diverge" in body
        assert (
            "Preço de compra: R$ 1.000,00" in body
            and "Preço de venda estimado: R$ 1.500,00" in body
        )
        before = target_messages(channel).copy()
        shell(
            instance,
            """from garimpei.infra.persistence.alert_models import FirstAlertIdentity
from garimpei.infra.persistence.listing_models import Listing
l=Listing.objects.get(external_id='16001');identity=FirstAlertIdentity.objects.select_related('intent__first_decision').get(listing=l)
assert identity.intent.confirmed_message and identity.intent.confirmed_ack
assert identity.intent.first_decision.assessment_id and identity.intent.first_decision.assessment_revision
""",
        )
        command(instance, "./scripts/stop.sh")
        command(instance, "./scripts/init.sh", "--disposable")
        shell(
            instance,
            "from garimpei.main import build_alert_handler;[build_alert_handler(stage).execute() for stage in ('adopt','refresh','reconcile','send')]",
        )
        assert target_messages(channel) == before


def test_activation_preserves_preexisting_confirmed_uncertain_and_terminal_history(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, clock, channel):
        source.rows["16001"]["description"] = "O aparelho funciona perfeitamente."
        clock.advance(61)
        from tests.integration.test_collection import completed

        completed(instance, 2)
        wait_first(channel, clock)
        before = target_messages(channel).copy()
        group = pause_worker(instance)
        try:
            shell(
                instance,
                """from datetime import timedelta
from django.utils.timezone import now
from garimpei.infra.persistence.listing_models import Listing,ListingEvent
from garimpei.infra.persistence.alert_models import AlertEventDecision,AlertIntent,AlertAttempt
l=Listing.objects.get(external_id='16002');event=ListingEvent.objects.create(listing=l,observation=l.latest,kind='discovered',silent=False,occurred_at=now()-timedelta(days=1))
decision=AlertEventDecision.objects.create(event=event,state='excluded',reason='legacy_terminal',next_action=now()+timedelta(days=1))
intent=AlertIntent.objects.create(decision=decision,state='uncertain',generation=1,session='synthetic',recipient='100@g.us',account='200@c.us',body='Corpo histórico de transmissão incerta',next_action=now()+timedelta(days=1),lease_until=now()+timedelta(days=1),created_at=now()-timedelta(days=1))
AlertAttempt.objects.create(intent=intent,ordinal=1,generation=1,authorized_at=now()-timedelta(days=1),state='uncertain')
""",
            )
            from tests.integration.test_collection import sql

            receipt_query = "SELECT id,state,body,confirmed_message,confirmed_ack,confirmed_at FROM runtime_alertintent ORDER BY id"
            attempts_query = (
                "SELECT id,intent_id,state,authorized_at FROM runtime_alertattempt ORDER BY id"
            )
            excluded_query = "SELECT id,state,reason FROM runtime_alerteventdecision WHERE reason='legacy_terminal'"
            receipts = sql(instance, receipt_query)
            attempts = sql(instance, attempts_query)
            excluded = sql(instance, excluded_query)
            with instance.private_file.open("a") as output:
                output.write("GARIMPEI_ASSESSMENT_ENABLED=true\n")
            shell(
                instance,
                "from garimpei.main import reconcile_assessments,build_alert_handler;reconcile_assessments();[build_alert_handler(stage).execute() for stage in ('adopt','refresh','reconcile','send')]",
            )
            assert sql(instance, receipt_query) == receipts
            assert sql(instance, attempts_query) == attempts
            assert sql(instance, excluded_query) == excluded
            assert target_messages(channel) == before
        finally:
            resume_worker(group)


def test_alert_note_keeps_damage_suspicion_and_manual_divergence(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path, enabled=False) as (
        instance,
        _source,
        _clock,
        channel,
    ):
        shell(
            instance,
            """from uuid import uuid4
from django.utils.timezone import now
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.assessment_models import ConditionAssessment
from garimpei.infra.repository.alert.assessment_note import assessment_note
l=Listing.objects.get(external_id='16001');identity=uuid4()
findings=[dict(dimension='appearance',assessment=kind,description=description,references=[]) for kind,description in [('clear_defect','Trinca no item principal'),('suspected','Possível oxidação'),('unknown','Área encoberta sem inspeção')]]
row=ConditionAssessment.objects.create(id=identity,listing=l,observation=l.latest,input_fingerprint='f'*64,policy_version='condition-policy-v1',prompt_version='condition-evidence-v1',schema_version='condition-evidence-v1',model_revision='controlled',input_snapshot={},generation=1,status='complete',condition='defect',sufficient=True,reason='clear_defect',result=dict(id=str(identity),condition='defect',sufficient=True,status='complete',revision=7,findings=findings),created_at=now(),updated_at=now())
note=assessment_note(identity,7)
for description in ('Trinca no item principal','Possível oxidação','Área encoberta sem inspeção'):assert description in note
assert 'Escolha manual' in note and 'diverge' in note
assert str(identity) in note and 'revisão 7' in note
""",
        )
        assert not target_messages(channel)
