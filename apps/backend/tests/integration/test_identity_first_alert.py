import time
from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import command, shell, wait_for


def test_identity_completion_authorizes_one_first_alert_and_preserves_receipt(
    tmp_path: Path,
) -> None:
    with first_eligibility_scenario(
        tmp_path,
        target_title="PlayStation 5 Slim disco",
        target_description="Usado. Funciona perfeitamente.",
    ) as (instance, source, clock, channel):
        worker = pause_worker(instance)
        try:
            assert not [call for call in channel.calls if call == ("POST", "/api/sendText")]
            shell(
                instance,
                """
from garimpei.main import build_identity_repository,build_read_profit
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
listing=Listing.objects.get(external_id='16001')
identity=build_identity_repository()
view=identity.read(listing.id)
assert view.result.state=='missing_attribute'
assert build_read_profit().execute(listing.id).resale.value is None
from garimpei.main import build_first_alert_store,_listing_clock
from garimpei.config.env import load_listing_settings
from garimpei.usecase.alert.refresh_first_eligibility_usecase import RefreshFirstEligibilityUseCase
clock=_listing_clock(load_listing_settings())
store=build_first_alert_store();store.adopt(clock())
RefreshFirstEligibilityUseCase(store,build_read_profit(),clock).execute()
assert FirstAlertIdentity.objects.get(listing=listing).reason=='atributo_ausente'

values=tuple(sorted(dict(family='playstation5',model='ps5',generation='slim',edition='disc',capacity='1tb').items()))
identity.save(IdentityEdit(listing.id,listing.latest.ordinal,0,'save',values))
assert identity.read(listing.id).result.state=='identified'
""",
            )
        finally:
            resume_worker(worker)
        next_advance = time.monotonic() + 6

        def confirmed() -> bool:
            nonlocal next_advance
            if time.monotonic() >= next_advance:
                clock.advance(6)
                next_advance = time.monotonic() + 6
            with instance.database() as database:
                result = database.execute(
                    "SELECT count(*) FROM runtime_alertintent i JOIN runtime_firstalertidentity f ON f.intent_id=i.id JOIN runtime_listing l ON l.id=f.listing_id WHERE l.external_id='16001' AND i.state='confirmed'"
                ).fetchone()
            return result == (1,)

        wait_for(confirmed, "F18 identity-first eligibility confirmation", seconds=40)
        shell(
            instance,
            """
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
row=FirstAlertIdentity.objects.get(listing__external_id='16001')
assert row.intent.state=='confirmed' and row.intent.confirmed_message and row.intent.confirmed_ack
assert row.intent.first_decision.cause=='automatic_input'
assert row.intent.first_decision.financial['profit']=='350.00'
assert row.decisions.filter(reason='atributo_ausente').exists()
assert row.decisions.filter(reason='eligible').exists()
""",
        )
        before = len([call for call in channel.calls if call == ("POST", "/api/sendText")])
        assert before == 1
        command(instance, "./scripts/stop.sh")
        command(instance, "./scripts/init.sh", "--disposable")
        clock.advance(5)
        shell(
            instance,
            """
from garimpei.main import build_identity_repository
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity
listing=Listing.objects.get(external_id='16001');store=build_identity_repository();view=store.read(listing.id)
store.save(IdentityEdit(listing.id,listing.latest.ordinal,view.result.manual_revision,'save',view.manual_values))
row=FirstAlertIdentity.objects.get(listing=listing)
assert row.intent.state=='confirmed' and row.intent.confirmed_message
""",
        )
        assert len([call for call in channel.calls if call == ("POST", "/api/sendText")]) == before


def test_identity_noop_does_not_bypass_manual_condition_exception(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, clock, channel):
        worker = pause_worker(instance)
        try:
            shell(
                instance,
                """
from garimpei.main import build_read_condition,build_classify_condition,build_alert_handler,build_identity_repository
from garimpei.domain.valuation.identity_ports import IdentityEdit
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.alert_models import FirstAlertIdentity,AlertIntent
from garimpei.infra.repository.alert.first_inputs import automatic_signature
l=Listing.objects.get(external_id='16001')
build_classify_condition().execute(l.id,'good',build_read_condition().execute(l.id).state.revision)
for stage in ('adopt','refresh','send'): build_alert_handler(stage).execute()
r=FirstAlertIdentity.objects.get(listing=l);assert r.reason=='manual_change_only' and r.intent_id is None
before=automatic_signature(l)
values=tuple(sorted(dict(family='playstation5',model='ps5',generation='slim',edition='disc',capacity='1tb').items()))
build_identity_repository().save(IdentityEdit(l.id,l.latest.ordinal,0,'save',values))
assert automatic_signature(l)==before,'A no-op identity correction changed effective input and bypassed manual condition suppression'
from garimpei.main import reconcile_valuations,build_valuation_handler
from garimpei.infra.persistence.valuation_models import ValuationWork
reconcile_valuations()
for work in list(ValuationWork.objects.filter(completed=False).values_list('id',flat=True)): build_valuation_handler().execute(work)
for stage in ('refresh','send'): build_alert_handler(stage).execute()
r.refresh_from_db();assert r.reason=='manual_change_only' and r.intent_id is None
assert not AlertIntent.objects.filter(first_decision__identity=r).exists()
""",
            )
        finally:
            resume_worker(worker)
        assert not [
            message for message in channel.messages if "/item/16001/" in str(message["body"])
        ]
