"""Additional contract fault boundaries, separate from the frozen full-suite inventory."""

from tests.factories.runtime import FoundationInstance
from tests.integration.test_media_persistence import media_instance as media_instance
from tests.integration.test_media_persistence import shell


def test_rejected_content_and_destination_leave_previous_copy_available(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
entry=MediaEntry.objects.get(capture_id=a['capture'],position=0);asset=entry.asset
store=build_media_store();original=queries.file(UUID(a['listing']),asset.id,'original')
before=store.read(original)
for url,reason in ((ORIGIN+'/invalid.bin','media_content_rejected'),('http://127.0.0.1:1/forbidden','media_destination_rejected')):
 entry.candidates=[dict(url=url)];entry.save()
 job=MediaJob.objects.get(entry=entry,kind='download');job.state='pending';job.next_at=now();job.save()
 runner.execute(job.id);entry.refresh_from_db();job.refresh_from_db()
 assert entry.reason==reason and job.reason==reason
 assert entry.asset_id==asset.id and store.read(original)==before
 assert queries.gallery(UUID(a['listing']),UUID(a['observation'])).state=='partial'
print('invalid content and forbidden destination persist specific partial reasons without losing prior bytes')
""",
    )


def test_expired_url_keeps_exact_previous_copy_and_does_not_mark_listing_removed(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
repo=build_media_repository();store=build_media_store()
entry=MediaEntry.objects.get(capture_id=a['capture'],position=0)
asset=entry.asset;original=queries.file(UUID(a['listing']),asset.id,'original')
before=store.read(original);obtained=asset.obtained_at
entry.candidates=[dict(url=ORIGIN+'/expired',width=1280,height=960)];entry.save()
job=MediaJob.objects.get(entry=entry,kind='download');job.state='pending';job.next_at=now();job.save()
runner.execute(job.id)
job.refresh_from_db();entry.refresh_from_db();asset.refresh_from_db()
assert job.refresh_requested and job.reason=='media_source_expired' and job.attempts==2
assert entry.asset_id==asset.id and entry.reason=='media_source_expired'
assert store.read(original)==before and asset.obtained_at==obtained
assert queries.gallery(UUID(a['listing']),UUID(a['observation'])).state=='partial'
assert ListingObservation.objects.get(id=a['observation']).evidence.get('source_available') is not False
# A repeated unit before its due date performs no transfer and preserves the old version.
runner.execute(job.id);job.refresh_from_db();assert job.attempts==2
print('expired CDN URL retains original bytes/date and schedules one owned-detail renewal')
""",
    )


def test_concurrent_claims_and_write_fault_preserve_quota_and_other_photo_progress(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
from concurrent.futures import ThreadPoolExecutor
from django.db import connections
from unittest.mock import patch
repo=build_media_repository();store=build_media_store()
first=MediaJob.objects.get(entry__capture_id=a['capture'],entry__position=0,kind='download')
second=MediaJob.objects.get(entry__capture_id=b['capture'],kind='download')
for job in (first,second):job.state='pending';job.next_at=now();job.save()
def claim(identity):
 try:return repo.claim(identity,now())
 finally:connections.close_all()
with ThreadPoolExecutor(2) as pool:claims=list(pool.map(claim,[first.id,second.id]))
assert sum(c is not None for c in claims)==1
assert sum(MediaJob.objects.values_list('reserved_bytes',flat=True))<=67108864
for result in claims:
 if result:repo.fail(result,'controlled_release',now())
first.refresh_from_db();first.next_at=now();first.save()
original=queries.file(UUID(a['listing']),gallery.photos[0].version_id,'original')
before=store.read(original)
with patch('garimpei.infra.gateway.media.local_store.LocalMediaStore._atomic',side_effect=OSError('controlled-write-fault')):
 runner.execute(first.id)
assert store.read(original)==before
first.refresh_from_db();assert first.reason=='media_write_failed' and first.reserved_bytes==0
second.refresh_from_db();second.next_at=now();second.save();runner.execute(second.id)
second.refresh_from_db();assert second.state=='done'
assert queries.gallery(UUID(b['listing']),UUID(b['observation'])).photos[0].state=='available'
print('concurrent quota/lease admission and disk-write failure preserve copies and independent progress')
""",
    )


def test_interrupted_unlink_is_resumed_without_a_false_removed_state_or_late_pin(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
from unittest.mock import patch
repo=build_media_repository();store=build_media_store()
listing=UUID(a['listing']);observation=UUID(a['observation']);version=gallery.photos[0].version_id
Listing.objects.filter(id=listing).update(media_tracking_active=False)
with patch('garimpei.infra.gateway.media.local_store.LocalMediaStore.remove',side_effect=OSError('interrupted-unlink')):
 CleanMediaUseCase(repo,store,now).execute()
asset=MediaAsset.objects.get(id=version)
assert asset.state=='removing' and asset.removed_at is None
try:repo.acquire(listing,observation,version,'ANALISE-A','late-pin',now())
except MediaError as failure:assert failure.status==409
else:raise AssertionError('late pin acquired removing bytes')
CleanMediaUseCase(repo,store,now).execute()
asset.refresh_from_db();assert asset.state=='removed' and asset.removed_at
assert not store._path(asset.key).exists() and not store._path(asset.key+'.thumb').exists()
assert ListingObservation.objects.filter(id=observation).exists()
print('interrupted cleanup remains removing until unlink succeeds; late pin conflicts')
""",
    )


def test_rename_before_commit_recovers_with_one_confirmed_version_and_no_double_charge(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
from garimpei.domain.media.media import Manifest,Photo,Variant
from garimpei.infra.repository.media.captures import create_capture
from garimpei.infra.persistence.listing_models import CollectionCycle
from garimpei.infra.repository.listing.mapper import encode_evidence
from garimpei.domain.listing.listing import Evidence
from garimpei.config.env import load_media_settings
from garimpei.infra.gateway.media.image_transport import BoundedImageTransport
import os
repo=build_media_repository();store=build_media_store();listing=Listing.objects.get(id=a['listing'])
old=listing.latest;cycle=CollectionCycle.objects.create(state=old.cycle.state,scope_key='media',revision=2)
observation=ListingObservation.objects.create(listing=listing,cycle=cycle,ordinal=2,observed_at=now(),evidence=encode_evidence(Evidence(title='crash-boundary')),coverage={})
listing.latest=observation;listing.ordinal=2;listing.save()
capture=create_capture(observation,Manifest('present',(Photo('crash-photo',(Variant(ORIGIN+'/other.png'),),True),),True,''),load_media_settings().policy,now())
job=MediaJob.objects.get(entry__capture=capture,kind='download');claim=repo.claim(job.id,now());assert claim
content=BoundedImageTransport(load_media_settings().policy,ORIGIN).fetch(ORIGIN+'/other.png')
key=store.put(claim,content)
assert store._path(key).exists() and not MediaAsset.objects.filter(listing=listing,photo_key='crash-photo').exists()
# Persisted crash cut point: file rename succeeded, no DB publication, owner lease expired.
MediaJob.objects.filter(id=job.id).update(lease_until=now()-timedelta(seconds=1))
os.utime(store._path(key),(0,0));repo.reconcile_orphans(store.reconcile_orphans,now())
runner.execute(job.id)
assert MediaAsset.objects.filter(listing=listing,photo_key='crash-photo',state='available').count()==1
new=queries.gallery(listing.id,observation.id).photos[0]
assert new.sha256==content.sha256 and store.read(queries.file(listing.id,new.version_id,'original'))==content.data
assert MediaJob.objects.get(id=job.id).reserved_bytes==0
assert queries.gallery(listing.id,old.id).photos[0].version_id==gallery.photos[0].version_id
print('rename-before-commit persisted cut point recovers once with exact content and historical protection')
""",
    )


def test_photo_count_and_variant_limits_remain_explicit_without_destroying_prior_copy(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
from dataclasses import replace
from garimpei.domain.media.media import Manifest,Photo,Variant
from garimpei.infra.repository.media.captures import create_capture
from garimpei.infra.persistence.listing_models import CollectionCycle
from garimpei.infra.repository.listing.mapper import encode_evidence
from garimpei.domain.listing.listing import Evidence
from garimpei.config.env import load_media_settings
from garimpei.infra.gateway.media.image_transport import BoundedImageTransport
from garimpei.infra.repository.media.postgres_repository import PostgresMediaRepository
from garimpei.infra.gateway.media.local_store import LocalMediaStore
from garimpei.usecase.media.obtain_media_usecase import ObtainMediaUseCase
settings=load_media_settings();policy=replace(settings.policy,max_file_bytes=5000,max_photos=1)
store=LocalMediaStore(settings.root,policy,settings.environment_id)
repo=PostgresMediaRepository(policy,store.used_bytes)
bounded_runner=ObtainMediaUseCase(repo,BoundedImageTransport(policy,ORIGIN),store,now)
listing=Listing.objects.get(id=a['listing']);old=listing.latest
cycle=CollectionCycle.objects.create(state=old.cycle.state,scope_key='media',revision=2)
observation=ListingObservation.objects.create(listing=listing,cycle=cycle,ordinal=2,observed_at=now(),evidence=encode_evidence(Evidence(title='bounded-gallery')),coverage={})
listing.latest=observation;listing.ordinal=2;listing.save()
variants=(Variant(ORIGIN+'/primary-large.jpg',1280,960),Variant(ORIGIN+'/primary-small.jpg',320,240))
photos=tuple(Photo('limited-'+str(index),variants,index==12) for index in range(13))
capture=create_capture(observation,Manifest('present',photos,True,''),policy,now())
assert capture.entries.count()==1 and capture.entries.get().photo_key=='limited-12'
assert capture.known_count==13 and not capture.complete
job=MediaJob.objects.get(entry__capture=capture,kind='download');bounded_runner.execute(job.id)
limited=queries.gallery(listing.id,observation.id)
assert limited.state=='partial' and not limited.complete and limited.known_count==13
assert limited.photos[0].width==320 and limited.photos[0].height==240
assert limited.photos[0].reason=='media_file_limit'
assert queries.gallery(listing.id,old.id).photos[0].width==1280
print('primary first,13->1 explicit count limit and large->small partial quality preserve historical original')
""",
    )
