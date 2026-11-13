from tests.factories.runtime import FoundationInstance
from tests.integration.test_collection import shell
from tests.integration.test_operational_recovery import operational_instance as operational_instance


def test_status_and_backup_keep_one_database_frontier_under_concurrent_commit(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from uuid import uuid4
from django.db import connection
from django.utils.timezone import now
from garimpei.infra.gateway.operations import snapshot_gateway
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.queries.operations.postgres_queries import PostgresOperationalQueries
from garimpei.main import build_operational_status,build_backup_repository
def write_listing(external):
 try:return Listing.objects.create(source='facebook_marketplace',external_id=external,canonical_url='https://www.facebook.com/marketplace/item/'+external+'/',first_seen_at=now(),origin='monitoring').id
 finally:connection.close()
original=PostgresOperationalQueries._counts
before=Listing.objects.count()
def during_counts(self,rows,stamp):
 with ThreadPoolExecutor(max_workers=1) as pool:pool.submit(write_listing,'1700901').result(timeout=10)
 return original(self,rows,stamp)
with patch.object(PostgresOperationalQueries,'_counts',during_counts):
 status=build_operational_status().execute()
assert status['counts']['stored']['value']==before and Listing.objects.count()==before+1
assert status['counts']['revalidated']['value']==6
assert build_operational_status().execute()['counts']['stored']['value']==before+1
capture_table=snapshot_gateway._capture_table
written=[]
def during_capture(model,fields):
 result=capture_table(model,fields)
 if model._meta.model_name=='monitoringconfiguration':
  with ThreadPoolExecutor(max_workers=1) as pool:written.append(pool.submit(write_listing,'1700902').result(timeout=10))
 return result
r=build_backup_repository()
with patch.object(snapshot_gateway,'_capture_table',during_capture):
 captured=r._snapshot.capture(str(uuid4()))
try:
 assert written and str(written[0]).encode() not in captured.files['runtime.listing.jsonl']
 r._snapshot.validate({'schema_hash':snapshot_gateway.schema_hash(),**captured.information},captured.files)
finally:captured.close()
later=r._snapshot.capture(str(uuid4()))
try:assert str(written[0]).encode() in later.files['runtime.listing.jsonl']
finally:later.close()
""",
    )


def test_native_media_and_analysis_use_real_pending_deadlines_and_confirmed_boundaries(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from datetime import timedelta
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.media_models import MediaCapture,MediaEntry,MediaJob
from garimpei.infra.persistence.inference_models import InferenceRequest,InferenceControl
from garimpei.main import build_operational_status,_listing_clock,_effective_listing_settings
stamp=_listing_clock(_effective_listing_settings())()
listing=Listing.objects.get(external_id='16001')
MediaCapture.objects.update(state='ready')
capture=MediaCapture.objects.get(observation_id=listing.latest_id)
capture.state='pending';capture.observed_at=stamp-timedelta(seconds=240);capture.save()
entry=MediaEntry.objects.create(capture=capture,photo_key='controlled-native-state',position=0,candidates=[])
job=MediaJob.objects.create(entry=entry,kind='download',next_at=stamp+timedelta(seconds=600))
def stage(name):return next(s for s in build_operational_status().execute()['stages'] if s['stage']==name)
assert stage('media')['state']=='waiting' and stage('media')['last_progress_at'] is None,stage('media')
job.next_at=stamp-timedelta(seconds=1);job.save()
assert stage('media')['state']=='stalled'
job.state='failed';job.save();capture.state='failed';capture.save()
assert stage('media')['state']=='suspended' and stage('media')['reason']=='media_attention_required'
InferenceControl.objects.update_or_create(pk=1,defaults={'service':True,'paused':False})
request=InferenceRequest.objects.create(observation_id=listing.latest_id,revision=1,signature='e'*64,artifact='controlled-state-fixture',prompt_version='local-evidence-v1',schema_version='local-evidence-v1',created_at=stamp-timedelta(seconds=240),next_attempt_at=stamp+timedelta(seconds=600),state='awaiting_resource')
assert stage('inference')['state']=='waiting' and stage('inference')['last_progress_at'] is None
request.state='succeeded';request.completed_at=stamp;request.save()
assert stage('inference')['state']=='idle' and stage('inference')['last_progress_at']==stamp
""",
    )
