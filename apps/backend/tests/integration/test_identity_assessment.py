"""Effective identity changes fence old visual assessments before the next worker turn."""

import pytest

from tests.factories.runtime import FoundationInstance
from tests.integration.test_media_persistence import media_instance as media_instance
from tests.integration.test_media_persistence import shell
from tests.integration.test_multimodal_condition import BOOT


def test_manual_identity_completion_invalidates_and_rebuilds_visual_assessment(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + """
from garimpei.main import build_save_identity
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.infra.queries.listing.assessment_queries import PostgresAssessmentQueries
obs.evidence=dict(obs.evidence,title='Produto usado');obs.save()
before=inputs.read(listing.id)
first=prepare.execute(listing.id)
for _ in range(3):run.execute()
assert complete.execute(first.id)
assert not build_read_condition().execute(listing.id).state.satisfies_alert_condition
values=tuple(sorted(dict(family='headphone',brand='jbl',model='tune520bt').items()))
view=build_save_identity().execute(IdentityEdit(listing.id,obs.ordinal,0,'save',values))
assert view.result.state=='identified'
after=inputs.read(listing.id)
assert after.fingerprint!=before.fingerprint, 'manual identity did not invalidate analysis input'
assert after.snapshot['identity']==view.result.product_key and after.snapshot['category']=='headphone'
current=PostgresAssessmentQueries().observation(listing.id,obs.id)
assert current.reason=='superseded_input' and current.previous==first.id
assert not current.sufficient
second=prepare.execute(listing.id)
assert second.id!=first.id and second.generation>first.generation
for _ in range(3):run.execute()
assert complete.execute(second.id)
current=build_read_condition().execute(listing.id).state
assert current.assessment.id==second.id and current.satisfies_alert_condition
assert ConditionAssessment.objects.get(id=first.id).status=='complete'
print('manual missing-to-known identity fences historical assessment immediately and recomputes current evidence PASS')
""",
    )


def test_recognized_family_without_category_word_and_equivalent_manual_input_keep_semantics(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + """
from garimpei.main import build_save_identity
from garimpei.domain.valuation.identity_ports import IdentityEdit
obs.evidence=dict(obs.evidence,title='JBL Tune 520BT');obs.save()
before=inputs.read(listing.id)
assert before.snapshot['category']=='headphone', 'recognized F18 family lost without category keyword'
values=tuple(sorted(dict(family='headphone',brand='jbl',model='tune520bt').items()))
view=build_save_identity().execute(IdentityEdit(listing.id,obs.ordinal,0,'save',values))
assert view.result.state=='identified'
after=inputs.read(listing.id)
assert before.fingerprint==after.fingerprint, 'equivalent identity metadata changed visual content'
from decimal import Decimal
obs.price=Decimal('125.00');obs.save(update_fields=['price'])
assert inputs.read(listing.id).fingerprint==before.fingerprint
print('recognized family supplies rubric without title keyword; equivalent manual and price-only changes reuse content PASS')
""",
    )


@pytest.mark.parametrize("version_field", ["prompt_version", "schema_version"])
def test_prompt_or_schema_change_immediately_retires_current_assessment_without_erasing_history(
    media_instance: tuple[FoundationInstance, str], version_field: str
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        BOOT
        + "\nVERSION_FIELD="
        + repr(version_field)
        + """
from garimpei.infra.queries.listing.assessment_queries import PostgresAssessmentQueries
first=prepare.execute(listing.id)
for _ in range(3):run.execute()
assert complete.execute(first.id)
assert build_read_condition().execute(listing.id).state.satisfies_alert_condition
row=ConditionAssessment.objects.get(id=first.id)
historical_result=row.result;calls=gateway.calls
ConditionAssessment.objects.filter(id=first.id).update(**{VERSION_FIELD:'condition-evidence-old'})
current=PostgresAssessmentQueries().observation(listing.id,obs.id)
assert current.reason=='superseded_input', 'old prompt/schema still authorized current evidence'
assert current.previous==first.id and not current.sufficient
condition=build_read_condition().execute(listing.id).state
assert not condition.satisfies_alert_condition and condition.assessment.previous==first.id
row.refresh_from_db()
assert row.status=='complete' and row.result==historical_result
assert gateway.calls==calls, 'public read invoked inference'
print('old prompt/schema is immediately inapplicable; confirmed historical result remains intact and no model executes PASS')
""",
    )
