from pathlib import Path

from tests.factories.first_eligibility import first_cases, first_eligibility_scenario
from tests.factories.runtime import pause_worker, resume_worker
from tests.integration.test_collection import shell


def test_populated_schema_migration_and_inventory_resume_after_hundred(tmp_path: Path) -> None:
    with first_eligibility_scenario(tmp_path) as (instance, source, _, channel):
        group = pause_worker(instance)
        try:
            before_calls = list(channel.calls)
            before_source_calls = list(source.calls)
            shell(
                instance,
                """
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from garimpei.main import build_first_alert_store,_listing_clock
from garimpei.config.env import load_listing_settings
now=_listing_clock(load_listing_settings())()
old_target=[('runtime','0014_merge_inference_and_financial_snapshot')]
executor=MigrationExecutor(connection);executor.migrate(old_target)
apps=executor.loader.project_state(old_target).apps
L=apps.get_model('runtime','Listing');O=apps.get_model('runtime','ListingObservation');E=apps.get_model('runtime','ListingEvent')
D=apps.get_model('runtime','AlertEventDecision');I=apps.get_model('runtime','AlertIntent');A=apps.get_model('runtime','AlertAttempt');M=apps.get_model('runtime','ManualCondition')
base=L.objects.select_related('latest').get(external_id='16001');sample=base.latest
count=COUNT
for index in range(count-6):
 row=L.objects.create(source='facebook_marketplace',external_id=str(16100+index),canonical_url=f'https://www.facebook.com/marketplace/item/{16100+index}/',first_seen_at=now,origin='initial',ordinal=1)
 obs=O.objects.create(listing=row,cycle_id=sample.cycle_id,ordinal=1,observed_at=now,price=sample.price,evidence=sample.evidence,coverage=sample.coverage,provenance=sample.provenance)
 row.latest_id=obs.id;row.save()
assert L.objects.count()==count
for index,row in enumerate(L.objects.select_related('latest').order_by('id')):
 event=E.objects.create(listing=row,observation=row.latest,kind='price_decreased' if index==0 else 'discovered',silent=False,occurred_at=now,publication_order=1)
 decision=D.objects.create(event=event,state='eligible',reason='eligible',financial={'legacy':index},next_action=now)
 intent=I.objects.create(decision=decision,body=f'LEGACY IMMUTABLE {index}',session='synthetic',account='200@c.us',recipient='100@g.us',financial={'legacy':index},state='confirmed',reason='send_response_ack',next_action=now,created_at=now,confirmed_at=now,confirmed_message=f'legacy-{index}',confirmed_ack=1)
 A.objects.create(intent=intent,ordinal=1,generation=1,authorized_at=now,state='confirmed',message_id=f'legacy-{index}',ack=1,finished_at=now)
M.objects.create(listing=base,choice='good',revision=1,updated_at=now)
frozen=list(I.objects.order_by('id').values_list('id','decision_id','body','financial','session','recipient','account','confirmed_message','confirmed_at','confirmed_ack'))
observations=list(O.objects.order_by('id').values_list('id','evidence','provenance','listing_id'))
assert not connection.introspection.table_names().__contains__('runtime_firstalertidentity')
executor=MigrationExecutor(connection);executor.migrate([('runtime','0015_first_eligibility')])
from garimpei.infra.persistence.alert_models import AlertIntent,AlertAttempt,FirstAlertInventory,FirstAlertIdentity
from garimpei.infra.persistence.listing_models import ListingObservation,ManualCondition
assert list(AlertIntent.objects.order_by('id').values_list('id','decision_id','body','financial','session','recipient','account','confirmed_message','confirmed_at','confirmed_ack'))==frozen
assert list(ListingObservation.objects.order_by('id').values_list('id','evidence','provenance','listing_id'))==observations
assert AlertAttempt.objects.filter(state='confirmed').count()==101
assert ManualCondition.objects.get(listing_id=base.id).choice=='good'
# Adoption executes current application code after verifying the historical migration.
executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes())
store=build_first_alert_store();store.adopt(now)
progress=FirstAlertInventory.objects.get();assert not progress.completed and progress.cursor is not None
assert FirstAlertIdentity.objects.count()==100
from garimpei.main import build_alert_store,build_read_profit,build_read_alert_diagnostic,build_read_listing_changes,_effective_alert_settings,_alert_policy
from garimpei.domain.alert.alert import Binding
from garimpei.infra.gateway.alert.waha_gateway import WahaGateway
from garimpei.usecase.alert.refresh_first_eligibility_usecase import RefreshFirstEligibilityUseCase
from garimpei.usecase.alert.send_alert_usecase import SendAlertUseCase
assert store.pending(now)==()
RefreshFirstEligibilityUseCase(store,build_read_profit(),lambda:now).execute()
known=FirstAlertIdentity.objects.first();delivery_store=build_alert_store();binding=Binding('synthetic','100@g.us','200@c.us')
assert delivery_store.claim(known.intent_id,binding,now,reconcile=False) is None
settings=_effective_alert_settings();gateway=WahaGateway(settings.url,settings.key,_alert_policy())
SendAlertUseCase(delivery_store,gateway,binding,build_read_listing_changes(),lambda:now).execute()
cursor=progress.cursor
# A fresh repository resumes from committed cursor; no process-local inventory is needed.
store=build_first_alert_store();store.adopt(now)
progress.refresh_from_db();assert progress.completed
assert FirstAlertIdentity.objects.count()==101
assert FirstAlertIdentity.objects.filter(intent__state='confirmed').count()==101
store.adopt(now)
assert AlertIntent.objects.count()==101
assert list(AlertIntent.objects.order_by('id').values_list('id','decision_id','body','financial','session','recipient','account','confirmed_message','confirmed_at','confirmed_ack'))==frozen
d=build_read_alert_diagnostic().execute(base.id,base.latest_id)
assert d.first_alert_state=='confirmed' and d.confirmed_at==now
assert d.intent_reference==AlertIntent.objects.get(decision__event__listing_id=base.id).id
assert d.history and d.history[0].state=='confirmed'
print('MigrationExecutor0014->0015;101 identities;100+1 adoption;original bodies/receipts/choices intact')
""".replace("COUNT", str(first_cases()["LEGADO"]["count"])),
            )
            assert source.calls == before_source_calls
            assert channel.calls == before_calls, (
                "migration and inventory must not query any external channel"
            )
        finally:
            resume_worker(group)
