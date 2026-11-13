from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest

from tests.factories.gold_driver import GoldDriver


@pytest.fixture
def gold_driver(tmp_path: Path) -> Iterator[GoldDriver]:
    driver = GoldDriver(tmp_path)
    try:
        yield driver
    finally:
        driver.close()


def test_gold_first_alert_is_qualified_once_and_body_explains_reference(
    gold_driver: GoldDriver,
) -> None:
    prepared = gold_driver.action("prepare", case="BASE")
    assert prepared["first_reason"] == "eligible"
    qualifications = cast(list[dict[str, object]], prepared["qualifications"])
    assert qualifications[-1]["state"] == "qualified"
    sent = gold_driver.action("send")
    messages = cast(list[dict[str, object]], sent["messages"])
    assert len(messages) == 1 and messages[0]["to"] == "100@g.us"
    body = str(messages[0]["body"])
    for label in (
        "Produto normalizado: PlayStation 5 Slim com leitor 1 TB",
        "Preço de compra: R$ 1.900,00",
        "Preço de venda estimado: R$ 3.000,00",
        "Lucro estimado: R$ 800,00",
        "5 anúncios usados equivalentes",
        "mediana dos preços pedidos",
        "não comprova venda",
    ):
        assert label in body
    assert gold_driver.action("send")["messages"] == messages
    gold_driver.shell("""
from garimpei.infra.persistence.alert_models import AlertAttempt, AlertIntent
from garimpei.infra.persistence.gold_models import GoldQualification
row=AlertIntent.objects.get(state='confirmed')
assert row.gold_qualification_id and row.confirmed_ack == 1
assert AlertAttempt.objects.get(intent=row).gold_policy_verified == 'gold-alert-v1'
assert GoldQualification.objects.get(id=row.gold_qualification_id).evidence['financial']['profit']=='800.00'
""")


@pytest.mark.parametrize(
    "case,reason",
    [
        ("NO_PHOTOS", "gold_photos_missing"),
        ("PROFIT_ZERO", "gold_profit_non_positive"),
        ("DEFECT", "gold_condition_defect"),
        ("HISTORY_FOUR", "gold_history_insufficient"),
    ],
)
def test_insufficient_conjunction_never_posts(
    gold_driver: GoldDriver, case: str, reason: str
) -> None:
    prepared = gold_driver.action("prepare", case=case)
    assert any(
        reason in cast(list[str], row["reasons"])
        for row in cast(list[dict[str, object]], prepared["qualifications"])
    )
    sent = gold_driver.action("send")
    assert sent["messages"] == [] and sent["attempts"] == 0


def test_queued_input_change_is_rechecked_at_final_authorization(gold_driver: GoldDriver) -> None:
    prepared = gold_driver.action("prepare", case="BASE")
    assert prepared["first_state"] == "eligible"
    gold_driver.action("mutate", field="description", value="O aparelho não liga. Com defeito.")
    sent = gold_driver.action("send")
    assert sent["messages"] == [] and sent["attempts"] == 0
    gold_driver.shell("""
from garimpei.infra.persistence.gold_models import GoldQualification
from garimpei.infra.persistence.listing_models import Listing
from garimpei.main import build_read_alert_diagnostic
l=Listing.objects.get(external_id='21001');d=build_read_alert_diagnostic().execute(l.id,l.latest_id)
assert d.gold and d.gold.state!='qualified'
assert GoldQualification.objects.filter(listing=l,state='qualified').exists()
""")


def test_policy_fence_rejects_incompatible_consumers_and_keeps_confirmed_history(
    gold_driver: GoldDriver,
) -> None:
    gold_driver.action("prepare", case="BASE")
    gold_driver.action("send")
    gold_driver.shell("""
from datetime import timedelta
from django.db import transaction,DatabaseError
from django.utils.timezone import now
from garimpei.infra.persistence.alert_models import AlertIntent,AlertAttempt
from garimpei.infra.repository.alert.gold_adoption import adopt_gold_policy
row=AlertIntent.objects.get(state='confirmed');before=(row.body,row.confirmed_message,row.confirmed_ack,row.confirmed_at)
assert adopt_gold_policy(now()) == adopt_gold_policy(now()+timedelta(seconds=1))
try:
 with transaction.atomic():
  AlertAttempt.objects.create(intent=row,ordinal=2,generation=2,authorized_at=now())
except DatabaseError:
 pass
else:
 raise AssertionError('incompatible consumer bypassed persistent gold fence')
row.refresh_from_db();assert (row.body,row.confirmed_message,row.confirmed_ack,row.confirmed_at)==before
assert AlertAttempt.objects.count()==1
""")
