"""Real PostgreSQL/authorization with named, finite synthetic I/O; no GPU claim."""

import json
from pathlib import Path
from typing import cast

import pytest

from tests.factories.gold_driver import GoldDriver

# Run inside GoldDriver's isolated Django process. F15 uses GoldConditionPreparer /
# ControlledConditionGateway, media origin and WAHA are owned loopback fixtures.
REVIEW_SCRIPT = r"""
import json
from io import StringIO
from django.core.management import call_command
from django.utils.timezone import now
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.gateway.assistance.snapshots import observation_snapshot
from garimpei.infra.persistence.assistance_models import AssistancePolicy, AssistanceReview
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.assessment_models import AssessmentHead
from garimpei.infra.repository.assistance.postgres_repository import PostgresAssistanceRepository
from garimpei.infra.repository.assistance.publication import current_review
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.usecase.inference.request_analysis_usecase import RequestAnalysisUseCase
from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase
from tests.factories.monitoring import require_disposable

require_disposable()
assert not AssistancePolicy.objects.filter(active=True).exists()

class NamedFiniteAssistancePreparer:
 def artifact(self): return 'f23-worker-authorization-controlled-v1'
 def prepare(self, value):
  return (PreparedPart('text', value.text, profile=value.prompt_version),)

class NamedProgrammedAssistanceProvider:
 calls = 0
 def infer(self, part, artifact):
  assert artifact == 'f23-worker-authorization-controlled-v1'
  snapshot = json.loads(part.text)
  self.calls += 1
  result = dict(outcome='supported', findings=[dict(field=f['field'], value=f['value'],
   evidence_refs=[f['id']], reason_code='explicit_evidence') for f in snapshot['facts']],
   limitations=['Programmed synthetic control; no model-quality or human-review claim'])
  return dict(content=json.dumps(result), metrics=dict(controlled_fake=True))
 def diagnose(self): return dict(service=True, resident=False, reason='controlled_fixture')
 def unload(self): return True
 def recover(self): return True

target=Listing.objects.select_related('latest').get(external_id='21001')
head=AssessmentHead.objects.select_related('current').get(listing=target)
assert head.current.sufficient and head.current.status=='complete'
inference=PostgresInferenceRepository(lambda:0,100)
repository=PostgresAssistanceRepository(RequestAnalysisUseCase(inference,NamedFiniteAssistancePreparer()))
provider=NamedProgrammedAssistanceProvider()
run=RunAnalysisUseCase(inference,provider,now)
reviews=[]
for candidate in Listing.objects.exclude(pk=target.id).select_related('latest').order_by('external_id'):
 snapshot=observation_snapshot(target,'comparables',candidate.latest)
 review=repository._create('comparables','listing_observation',target.latest.id,
  target.latest.ordinal,snapshot,target.latest,candidate.latest)
 assert run.execute(), 'programmed comparable result did not publish'
 repository._complete(review)
 review.refresh_from_db()
 assert review.state=='supported' and current_review(review)
 reviews.append(str(review.id))
assert len(reviews)==5
snapshot=observation_snapshot(target,'identity')
identity=repository._create('identity','listing_observation',target.latest.id,
 target.latest.ordinal,snapshot,target.latest)
if COMPLETE_IDENTITY:
 assert run.execute(), 'programmed identity result did not publish'
 repository._complete(identity)
 identity.refresh_from_db()
 assert identity.state=='supported' and current_review(identity)
else:
 assert identity.state=='pending' and identity.result is None
call_command('assistance_policy',activate=True,evaluation=True,stdout=StringIO())
assert AssistancePolicy.objects.filter(pk=1,active=True).exists()
print('CONTROLLED_REVIEW_EVIDENCE='+json.dumps(dict(
 policy='assisted-evidence-v1', provider='NamedProgrammedAssistanceProvider',
 preparer='NamedFiniteAssistancePreparer', provider_calls=provider.calls,
 comparable_reviews=reviews, identity_review=str(identity.id), identity_state=identity.state,
 assessment=str(head.current_id), assessment_sufficient=head.current.sufficient,
 gpu_calls=0, independent_human_labels=False)))
"""

FROZEN_SCRIPT = r"""
import json
from django.db import transaction, DatabaseError
from django.utils.timezone import now
from garimpei.infra.persistence.alert_models import AlertAttempt, AlertIntent
from garimpei.infra.persistence.gold_models import GoldQualification
from garimpei.infra.persistence.assistance_models import AssistanceReview
row=AlertIntent.objects.get(state='confirmed')
attempt=AlertAttempt.objects.get(intent=row)
qualification=GoldQualification.objects.get(pk=row.gold_qualification_id)
assert attempt.gold_policy_verified=='assisted-evidence-v1'
assert qualification.state=='qualified' and qualification.policy=='assisted-evidence-v1'
assert qualification.evidence['assistance']['policy']=='assisted-evidence-v1'
assert len(qualification.evidence['assistance']['reviews'])==6
assert not qualification.evidence['assistance']['missing']
assert row.confirmed_ack==1 and row.confirmed_message
assert row.financial['profit']==EXPECTED_PROFIT
assert len(AssistanceReview.objects.filter(state='supported'))==6
for incompatible in (None, 'gold-alert-v1'):
 try:
  with transaction.atomic():
   AlertAttempt.objects.create(intent=row, ordinal=2, generation=2,
    authorized_at=now(), gold_policy_verified=incompatible)
 except DatabaseError as error:
  assert 'gold consumer incompatible' in str(error)
 else:
  raise AssertionError('incompatible policy marker bypassed SQL authorization fence')
assert AlertAttempt.objects.count()==1
try:
 with transaction.atomic():
  legacy=GoldQualification.objects.create(listing=qualification.listing,
   observation=qualification.observation, purpose_key='controlled-policy-mismatch',
   policy='gold-alert-v1', input_fingerprint=qualification.input_fingerprint,
   state='qualified', reason='eligible', reasons=[], evidence=qualification.evidence,
   evaluated_at=qualification.evaluated_at, valid_until=qualification.valid_until)
  mismatched=AlertIntent.objects.create(gold_qualification=legacy,
   next_action=now(), created_at=now())
  AlertAttempt.objects.create(intent=mismatched, ordinal=1, generation=1,
   authorized_at=now(), gold_policy_verified='assisted-evidence-v1')
except DatabaseError as error:
 assert 'gold qualification required' in str(error)
else:
 raise AssertionError('legacy qualification bypassed active F23 SQL fence')
assert AlertAttempt.objects.count()==1
print('CONTROLLED_FROZEN_EVIDENCE='+json.dumps(dict(body=row.body, financial=row.financial,
 session=row.session, recipient=row.recipient, account=row.account,
 qualification=str(qualification.id), qualification_fingerprint=qualification.input_fingerprint,
 attempt_policy=attempt.gold_policy_verified, confirmed_message=row.confirmed_message,
 confirmed_ack=row.confirmed_ack),default=str,sort_keys=True))
"""


def _evidence(output: str, prefix: str) -> dict[str, object]:
    line = next(line for line in output.splitlines() if line.startswith(prefix))
    return cast(dict[str, object], json.loads(line.removeprefix(prefix)))


@pytest.mark.parametrize(("case", "profit"), [("BASE", "800.00"), ("PROFIT_CENT", "0.01")])
def test_assisted_policy_authorizes_once_with_frozen_cents_and_destination(
    tmp_path: Path, case: str, profit: str
) -> None:
    driver = GoldDriver(tmp_path)
    try:
        assert driver.action("prepare", case=case)["first_state"] == "eligible"
        review_evidence = _evidence(
            driver.shell("COMPLETE_IDENTITY=True\n" + REVIEW_SCRIPT),
            "CONTROLLED_REVIEW_EVIDENCE=",
        )
        assert review_evidence["provider_calls"] == 6
        driver.action("revalue")
        driver.action("refresh")
        sent = driver.action("send")
        messages = cast(list[dict[str, object]], sent["messages"])
        assert sent["attempts"] == sent["post_count"] == len(messages) == 1
        assert messages[0]["to"] == "100@g.us"
        body = str(messages[0]["body"])
        for text in (
            "Produto normalizado: PlayStation 5 Slim com leitor 1 TB",
            "Preço de venda estimado: R$ 3.000,00",
            "5 anúncios usados equivalentes",
            "mediana dos preços pedidos",
            "não comprova venda",
            "Lucro estimado: R$ " + ("0,01" if profit == "0.01" else "800,00"),
        ):
            assert text in body
        inspect = "EXPECTED_PROFIT=" + repr(profit) + "\n" + FROZEN_SCRIPT
        frozen = _evidence(driver.shell(inspect), "CONTROLLED_FROZEN_EVIDENCE=")
        assert frozen["body"] == body
        assert (frozen["session"], frozen["recipient"], frozen["account"]) == (
            "synthetic",
            "100@g.us",
            "200@c.us",
        )
        driver.action("refresh")
        repeat = driver.action("send")
        assert repeat["messages"] == messages
        assert repeat["post_count"] == repeat["attempts"] == 1
        assert _evidence(driver.shell(inspect), "CONTROLLED_FROZEN_EVIDENCE=") == frozen
        print(
            json.dumps(
                dict(
                    case=case,
                    reviews=review_evidence,
                    frozen=frozen,
                    posts=1,
                    repeated_posts=0,
                    real_whatsapp_posts=0,
                ),
                sort_keys=True,
            )
        )
    finally:
        driver.close()


def test_pending_identity_review_blocks_final_assisted_authorization(tmp_path: Path) -> None:
    driver = GoldDriver(tmp_path)
    try:
        driver.action("prepare", case="BASE")
        evidence = _evidence(
            driver.shell("COMPLETE_IDENTITY=False\n" + REVIEW_SCRIPT),
            "CONTROLLED_REVIEW_EVIDENCE=",
        )
        assert evidence["provider_calls"] == 5 and evidence["identity_state"] == "pending"
        driver.action("revalue")
        driver.action("refresh")
        sent = driver.action("send")
        assert sent["messages"] == [] and sent["post_count"] == sent["attempts"] == 0
        rows = cast(list[dict[str, object]], sent["qualifications"])
        assert "assistance_identity_pending" in cast(list[str], rows[-1]["reasons"])
        assert driver.action("send")["post_count"] == 0
        print(
            json.dumps(
                dict(
                    case="PENDING_IDENTITY",
                    reviews=evidence,
                    posts=0,
                    attempts=0,
                    real_whatsapp_posts=0,
                ),
                sort_keys=True,
            )
        )
    finally:
        driver.close()


MIXED_POLICY_SCRIPT = r"""
import json
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction, DatabaseError
from django.utils.timezone import now
from garimpei.infra.persistence.alert_models import AlertAttempt, AlertIntent
from garimpei.infra.persistence.assistance_models import AssistancePolicy
from garimpei.infra.persistence.gold_models import GoldPolicyAdoption
from tests.factories.monitoring import require_disposable
require_disposable()
assert not AssistancePolicy.objects.filter(active=True).exists()
if GOLD_STATE=='missing':
 GoldPolicyAdoption.objects.filter(installation='local').delete()
else:
 GoldPolicyAdoption.objects.filter(installation='local').update(state='pending')
blocked=False
try:
 call_command('assistance_policy',activate=True,evaluation=True,stdout=StringIO())
except CommandError:
 blocked=True
# Deliberately corrupt only this disposable fixture to test the independent SQL fence.
AssistancePolicy.objects.update_or_create(pk=1,defaults=dict(active=True,adopted_at=now()))
intent=AlertIntent.objects.get(state='queued')
markers={}
for marker in (None,'gold-alert-v1','assisted-evidence-v1'):
 rejected=False
 try:
  with transaction.atomic():
   AlertAttempt.objects.create(intent=intent,ordinal=1,generation=1,
    authorized_at=now(),gold_policy_verified=marker)
   transaction.set_rollback(True)
 except DatabaseError:
  rejected=True
 markers[str(marker)]=rejected
assert AlertAttempt.objects.count()==0
print('CONTROLLED_MIXED_POLICY='+json.dumps(dict(gold_state=GOLD_STATE,
 activation_blocked=blocked,markers_rejected=markers,attempts=0)))
"""


@pytest.mark.parametrize("gold_state", ["pending", "missing"])
def test_assisted_adoption_and_sql_fence_require_active_gold_policy(
    tmp_path: Path, gold_state: str
) -> None:
    driver = GoldDriver(tmp_path)
    try:
        driver.action("prepare", case="BASE")
        evidence = _evidence(
            driver.shell("GOLD_STATE=" + repr(gold_state) + "\n" + MIXED_POLICY_SCRIPT),
            "CONTROLLED_MIXED_POLICY=",
        )
        print(json.dumps(evidence, sort_keys=True))
        assert evidence["activation_blocked"], "F23 adoption accepted inactive/missing F21 policy"
        assert all(cast(dict[str, bool], evidence["markers_rejected"]).values()), (
            "SQL fence accepted F23 authorization with inactive/missing F21 policy"
        )
        sent = driver.action("status")
        assert sent["messages"] == [] and sent["post_count"] == sent["attempts"] == 0
    finally:
        driver.close()
