from pathlib import Path
import sys
root=Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'apps/backend'))
from tests.factories.runtime import FoundationInstance,pause_worker,resume_worker
from tests.integration.test_collection import shell
instance=FoundationInstance(root,Path((root/'.runtime/f18-execution/envfile-path.txt').read_text().strip()))
worker=pause_worker(instance)
try:
 shell(instance,"""
import json,hashlib
from dataclasses import replace
from django.utils.timezone import now
from garimpei.main import build_read_monitoring_configuration
from garimpei.domain.listing.scope import Scope
from garimpei.infra.repository.listing.postgres_repository import PostgresCollectionRepository
from garimpei.infra.persistence.listing_models import Listing,ListingInterestMatch,ListingEvent,CollectionCycle,CollectionState,ManualCondition
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration,MonitoringInterest
from garimpei.infra.persistence.identity_models import ManualIdentityRevision
from garimpei.infra.persistence.alert_models import AlertIntent,AlertAttempt
from tests.factories.comparable_research import candidate
at=now();cfg=build_read_monitoring_configuration();scope=Scope.from_snapshot(cfg.execute())
assert scope is not None
confirmed=AlertIntent.objects.create(state='confirmed',body='protected confirmed fake body',created_at=at,next_action=at,confirmed_at=at,confirmed_message='fake-protected-confirmed',confirmed_ack=1)
uncertain=AlertIntent.objects.create(state='uncertain',body='protected uncertain fake body',created_at=at,next_action=at)
AlertAttempt.objects.create(intent=uncertain,ordinal=1,generation=1,authorized_at=at,state='uncertain',reason='transmission_possible')
def snapshot():
 return json.dumps([list(m.objects.order_by('pk').values()) for m in (MonitoringConfiguration,MonitoringInterest,ManualCondition,ManualIdentityRevision,AlertIntent,AlertAttempt)],sort_keys=True,default=str)
before=snapshot()
state=CollectionState.objects.get(configuration_id=scope.configuration_id,source=scope.source)
cycle=CollectionCycle.objects.create(state=state,scope_key=scope.key,revision=scope.revision,phase='running',started_at=at)
store=PostgresCollectionRepository(cfg,lambda:at,lambda *_:0,40)
reference=store.publish_reference(scope,cycle,candidate('19780'))
assert reference.listing.origin=='reference'
assert not ListingInterestMatch.objects.filter(observation=reference).exists()
assert not ListingEvent.objects.filter(listing=reference.listing).exists()
known=Listing.objects.get(external_id='19702')
events=ListingEvent.objects.filter(listing=known,kind='price_decreased').count()
observation=store.publish_reference(scope,cycle,candidate('19702','900'))
known.refresh_from_db()
assert known.origin!='reference' and observation.matches.exists()
assert ListingEvent.objects.filter(listing=known,kind='price_decreased').count()==events+1
assert snapshot()==before,'Research changed protected configuration/manual state/receipts/bodies'
""")
 print('PRESERVATION_PASS confirmedreceipt+uncertainattempt/body/config/interests/manualhistory unchanged; reference-only nofakeevent/match; knownactive match normalprice_decreased1')
finally: resume_worker(worker)
