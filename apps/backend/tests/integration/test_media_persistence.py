from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.factories.media import generate_corpus, prepare_media_instance, serve_media
from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker


@pytest.fixture(scope="module")
def media_instance(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[FoundationInstance, str]]:
    generate_corpus()
    root = Path(__file__).resolve().parents[4]
    with serve_media() as (origin, _):
        instance = prepare_media_instance(root, tmp_path_factory.mktemp("media-database"), origin)
        result = instance.command("./scripts/init.sh", "--disposable")
        assert result.returncode == 0, result.stdout + result.stderr
        group = pause_worker(instance)
        try:
            yield instance, origin
        finally:
            resume_worker(group)
            stopped = instance.command("./scripts/stop.sh", "--clean")
            assert stopped.returncode == 0, stopped.stdout + stopped.stderr


BOOTSTRAP = """
from datetime import timedelta
from uuid import UUID
from django.utils.timezone import now
from django.db import connection
from garimpei.infra.persistence.listing_models import Listing, ListingObservation, CollectionState
from garimpei.infra.persistence.media_models import MediaAsset, MediaCapture, MediaEntry, MediaJob, MediaReference
from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
from garimpei.main import build_media_runner, build_media_repository, build_media_store
from garimpei.domain.media.errors import MediaError
from garimpei.usecase.media.read_gallery_usecase import ReadMediaGalleryUseCase
from garimpei.usecase.media.acquire_media_usecase import AcquireMediaForAnalysisUseCase
from garimpei.usecase.media.release_reference_usecase import ReleaseMediaReferenceUseCase
from garimpei.usecase.media.clean_media_usecase import CleanMediaUseCase
from garimpei.domain.media.media import MediaFile
from tests.factories.media import seed_media_cases, inspect_media_cases
with connection.cursor() as c:
    c.execute('TRUNCATE runtime_listing, runtime_collectionstate CASCADE')
cases = seed_media_cases(ORIGIN)
assert not MediaCapture.objects.get(id=cases['A']['capture']).complete
runner = build_media_runner()
for _ in range(3):
    for identity in build_media_repository().due(now()):
        runner.execute(identity)
queries = PostgresMediaQueries()
a = cases['A']; b = cases['B']
gallery = ReadMediaGalleryUseCase(queries).execute(UUID(a['listing']), UUID(a['observation']))
assert len(gallery.photos) == 2
assert gallery.photos[0].width == 1280 and gallery.photos[0].height == 960
assert gallery.photos[0].thumbnail_state == 'ready'
assert all(p.state == 'available' for p in gallery.photos)
"""


def shell(instance: FoundationInstance, origin: str, code: str) -> str:
    result = instance.shell("ORIGIN=" + repr(origin) + "\n" + BOOTSTRAP + code)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_download_gallery_exact_bytes_revalidation_isolation_and_unavailability(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
import hashlib
from django.test import Client
client=Client(HTTP_HOST="127.0.0.1")
photo=gallery.photos[0]
path=f"/ofertas/{a['listing']}/imagens/{photo.version_id}/original/"
response=client.get(path)
assert response.status_code == 200
assert hashlib.sha256(response.content).hexdigest() == photo.sha256
assert response['Content-Length'] == str(len(response.content))
assert response['Cache-Control']=='private, no-cache'
assert response['X-Content-Type-Options']=='nosniff'
assert client.head(path).content == b''
assert client.get(path,HTTP_IF_NONE_MATCH=response['ETag']).status_code == 304
assert client.get(path.replace(a['listing'],b['listing'])).status_code == 404
assert client.get(path.replace('/original/','/invalid/')).status_code == 404
asset=MediaAsset.objects.get(id=photo.version_id)
asset.thumbnail_state='pending';asset.save()
assert client.get(path.replace('/original/','/miniatura/')).status_code == 503
build_media_store()._path(asset.key).unlink()
assert client.get(path).status_code == 503
assert MediaEntry.objects.filter(capture_id=a['capture']).count()==2
print('HTTP bytes, hash, HEAD,304,404,503 PASS')
""",
    )


def test_analysis_reference_idempotency_protection_cleanup_and_tombstone(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
from django.test import Client
repo=build_media_repository()
backup=repo.protected_versions('backup1',now())
assert backup
for pinned in backup: repo.release(pinned.reference_id,now())
acquire=AcquireMediaForAnalysisUseCase(repo,now)
release=ReleaseMediaReferenceUseCase(repo,now)
p=gallery.photos[0]
reference=acquire.execute(UUID(a['listing']),UUID(a['observation']),p.version_id,'ANALISE-A','run1')
assert acquire.execute(UUID(a['listing']),UUID(a['observation']),p.version_id,'ANALISE-A','run1').reference_id==reference.reference_id
Listing.objects.filter(id=a['listing']).update(media_tracking_active=False)
CleanMediaUseCase(repo,build_media_store(),now).execute()
assert queries.file(UUID(a['listing']),p.version_id,'original').sha256==p.sha256
release.execute(reference.reference_id);release.execute(reference.reference_id)
files=repo.cleanable(now())
assert any(f.version_id==p.version_id for f in files)
try:
    acquire.execute(UUID(a['listing']),UUID(a['observation']),p.version_id,'ANALISE-A','late')
except MediaError as exc: assert exc.status==409
else: raise AssertionError('removed version acquired')
CleanMediaUseCase(repo,build_media_store(),now).execute()
assert Client(HTTP_HOST="127.0.0.1").get(f"/ofertas/{a['listing']}/imagens/{p.version_id}/original/").status_code==410
asset=MediaAsset.objects.get(id=p.version_id)
assert asset.sha256==p.sha256 and asset.removed_at and asset.reason=='media_retention_ended'
assert ListingObservation.objects.filter(id=a['observation']).exists()
assert queries.gallery(UUID(b['listing']),UUID(b['observation'])).photos[0].state=='available'
print('analysis pins OR tracking, race, cleanup,tombstone PASS')
""",
    )


def test_old_observation_result_does_not_replace_new_capture_and_thumbnail_retry(
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
from garimpei.config.env import load_media_settings
from garimpei.infra.repository.listing.mapper import encode_evidence
from garimpei.domain.listing.listing import Evidence
listing=Listing.objects.get(id=a['listing'])
old=ListingObservation.objects.get(id=a['observation'])
from garimpei.infra.persistence.listing_models import CollectionCycle
newcycle=CollectionCycle.objects.create(state=old.cycle.state,scope_key='media',revision=2)
new=ListingObservation.objects.create(listing=listing,cycle=newcycle,ordinal=2,observed_at=now(),evidence=encode_evidence(Evidence(title='New')),coverage={})
listing.latest=new;listing.ordinal=2;listing.save()
cap=create_capture(new,Manifest('present',(Photo('new',(Variant(ORIGIN+'/other.png'),),True),),True,''),load_media_settings().policy,now())
for _ in range(3):
    for identity in build_media_repository().due(now()):runner.execute(identity)
assert queries.gallery(listing.id,new.id).photos[0].width==900
assert queries.gallery(listing.id,old.id).photos[0].width==1280
try:build_media_repository().retry(listing.id,UUID(a['capture']),queries.gallery(listing.id,old.id).revision,now())
except MediaError as exc:assert exc.code=='MEDIA_REVISION_CONFLICT'
else:raise AssertionError('recovery accepted superseded observation')
try:queries.gallery(listing.id,old.id,999999)
except MediaError as exc:assert exc.status==409
else:raise AssertionError('revision conflict ignored')
asset=MediaAsset.objects.get(id=gallery.photos[0].version_id)
original_hash=asset.sha256
asset.thumbnail_state='failed';asset.save()
job=MediaJob.objects.filter(entry__asset=asset,kind='thumbnail').first()
job.state='pending';job.next_at=now();job.attempts=0;job.save()
runner.execute(job.id)
asset.refresh_from_db();assert asset.thumbnail_state=='ready' and asset.sha256==original_hash
print('observation isolation and derivation recovery PASS')
""",
    )


def test_bounded_retries_generation_and_quota_reservations(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
from dataclasses import replace
from garimpei.infra.repository.media.postgres_repository import PostgresMediaRepository
from garimpei.config.env import load_media_settings
repo=build_media_repository()
failed=MediaJob.objects.get(entry__capture_id=cases['FALHA']['capture'],kind='download')
assert failed.attempts==1 and (failed.next_at-now()).total_seconds()>172790
for n in range(3):
    failed.next_at=now();failed.save();runner.execute(failed.id);failed.refresh_from_db()
assert failed.attempts==4 and failed.state=='failed'
runner.execute(failed.id);failed.refresh_from_db();assert failed.attempts==4
entry=MediaEntry.objects.get(capture_id=a['capture'],position=0)
job=MediaJob.objects.get(entry=entry,kind='download');job.state='pending';job.next_at=now();job.save()
limited=PostgresMediaRepository(replace(load_media_settings().policy,budget_bytes=1),lambda:0)
assert limited.claim(job.id,now()) is None
assert MediaCapture.objects.get(id=a['capture']).reason=='media_storage_budget'
claim=repo.claim(job.id,now());assert claim
assert repo.claim(job.id,now()) is None
old=now()-timedelta(seconds=1)
MediaJob.objects.filter(id=job.id).update(lease_until=old)
second=repo.claim(job.id,now());assert second and second.generation>claim.generation
try:repo.fail(claim,'stale',now())
except MediaError as exc:assert exc.code=='media_stale_generation'
else:raise AssertionError('stale owner accepted')
repo.fail(second,'controlled',now())
assert MediaJob.objects.get(id=job.id).reserved_bytes==0
print('4 bounded attempts, source retry-after,quota,lease fencing PASS')
""",
    )


def test_same_bytes_different_photo_keys_cannot_delete_pinned_original(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
from garimpei.domain.media.media import MediaClaim,Transfer
from uuid import uuid4
repo=build_media_repository();store=build_media_store()
p=gallery.photos[0];asset=MediaAsset.objects.get(id=p.version_id)
file=queries.file(UUID(a['listing']),p.version_id,'original');data=store.read(file)
claim=MediaClaim(uuid4(),1,'download',UUID(a['listing']),UUID(a['observation']),uuid4(),'different-photo-key',(),1)
content=Transfer(data,asset.mime,asset.width,asset.height,asset.sha256)
other_key=store.put(claim,content)
assert other_key!=asset.key
other=MediaAsset.objects.create(listing_id=a['listing'],photo_key=claim.photo_key,sha256=asset.sha256,mime=asset.mime,width=asset.width,height=asset.height,byte_count=asset.byte_count,key=other_key,obtained_at=now())
reference=repo.acquire(UUID(a['listing']),UUID(a['observation']),asset.id,'ANALISE-A','collision',now())
Listing.objects.filter(id=a['listing']).update(media_tracking_active=False)
CleanMediaUseCase(repo,store,now).execute()
other.refresh_from_db();assert other.state=='removed'
assert store.read(file)==data
repo.release(reference.reference_id,now())
print('same content/different photos retain independent physical protection PASS')
""",
    )


def test_recovery_http_validation_csrf_conflict_and_no_inline_transfer(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
from django.test import Client,RequestFactory
from django.middleware.csrf import get_token
from unittest.mock import patch
from dataclasses import replace
from garimpei.infra.http.media.media_handler import MediaHandler
from garimpei.usecase.media.request_recovery_usecase import RequestMediaRecoveryUseCase
from garimpei.infra.repository.media.postgres_repository import PostgresMediaRepository
from garimpei.config.env import load_media_settings
path=f"/ofertas/{a['listing']}/imagens/reprocessar/?pagina=2&q=fone"
client=Client(HTTP_HOST='127.0.0.1',enforce_csrf_checks=True)
assert client.post(path,{}).status_code==403
request=RequestFactory().get('/');token=get_token(request)
client.cookies['csrftoken']=request.META['CSRF_COOKIE']
valid=dict(media_capture=a['capture'],media_revision=str(gallery.revision),csrfmiddlewaretoken=token)
assert client.post(path,dict(valid,media_revision='bad')).status_code==400
assert client.post(path,dict(valid,media_capture=b['capture'])).status_code==404
assert client.post(path,dict(valid,media_revision='999999')).status_code==409
with patch('garimpei.infra.gateway.media.image_transport.BoundedImageTransport.fetch',side_effect=AssertionError('web performed download')):
    response=client.post(path,valid)
assert response.status_code==303 and 'pagina=2' in response['Location'] and 'q=fone' in response['Location']
assert client.post(path,valid).status_code==303
policy=replace(load_media_settings().policy,budget_bytes=None)
handler=MediaHandler(queries,build_media_store(),RequestMediaRecoveryUseCase(PostgresMediaRepository(policy,lambda:0),now))
with patch('garimpei.infra.http.media.routes.build_media_handler',return_value=handler):
    assert client.post(path,valid).status_code==409
print('recovery validation/CSRF/404/409/303/async-only PASS')
""",
    )


def test_legacy_detail_backfill_does_not_require_search_rediscovery(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    from tests.factories.listing import Source, serve

    class AbsentSearchSource(Source):
        def respond(self, path: str, parameters: dict[str, str]) -> tuple[int, dict[str, object]]:
            self.calls.append((path, parameters.copy()))
            if path.startswith("/detail/"):
                return 200, dict(
                    url="https://www.facebook.com/marketplace/item/11/",
                    title="PlayStation 5 usado",
                    description="Funciona bem",
                    context_cep=parameters["cep"],
                    media=dict(
                        presence="present",
                        complete=True,
                        reason="",
                        photos=[
                            dict(
                                key="legacy-photo",
                                primary=True,
                                correlated=True,
                                variants=[dict(url=origin + "/other.png", width=900, height=900)],
                            )
                        ],
                    ),
                )
            return 200, dict(
                context={k: v for k, v in parameters.items() if k != "page"},
                cards=[],
                next=None,
                end=True,
                empty=True,
            )

    instance, origin = media_instance
    source = AbsentSearchSource()
    with serve(source) as source_url:
        shell(
            instance,
            origin,
            """
from garimpei.main import _navigation_collection,_effective_listing_settings,_listing_policy,build_read_monitoring_configuration
from tests.factories.monitoring import prepare_state
from garimpei.domain.listing.scope import Scope
from garimpei.domain.listing.ports import Attempt
from garimpei.infra.gateway.listing.fixture_source import FixtureSource
from garimpei.infra.persistence.listing_models import ListingInterestMatch,ListingEvent
from garimpei.infra.persistence.media_models import MediaCapture
from garimpei.infra.persistence.listing_models import ManualCondition
prepare_state('ATIVA')
config=build_read_monitoring_configuration().execute();scope=Scope.from_snapshot(config)
legacy=cases['LEGADO'];listing=Listing.objects.get(id=legacy['listing']);observation=listing.latest
state=observation.cycle.state;state.source=scope.source;state.configuration_id=scope.configuration_id;state.initial_completed_at=now();state.save()
listing.source=scope.source;listing.save()
ListingInterestMatch.objects.create(observation=observation,kind=scope.searches[0].interest.kind,key=scope.searches[0].interest.key)
ManualCondition.objects.create(listing=listing,choice='good',revision=1,updated_at=now())
baseline=list(ListingEvent.objects.values_list('id','kind'))
repo=build_media_repository();repo.backfill(now())
settings=_effective_listing_settings();collection=_navigation_collection(settings)
collection.reconcile(_listing_policy(settings));state.refresh_from_db()
attempt=Attempt(state.current_id,state.generation);work=collection.begin(attempt)
source=FixtureSource(SOURCE_URL,20)
page=source.search(scope,scope.searches[0],None);assert page.candidates==()
target=next(t for t in collection.detail_targets(attempt) if t.external_id=='11')
candidate=source.detail(scope,target.external_id)
collection.stage(attempt,'detail:11',(candidate,))
collection.record(attempt,'detail:11',None)
assert collection.publish_batch(attempt,ready_only=True)
listing.refresh_from_db();assert listing.latest_id!=observation.id
for _ in range(3):
 for job in repo.due(now()):runner.execute(job)
recovered=queries.gallery(listing.id,listing.latest_id)
assert recovered.photos[0].width==900 and recovered.photos[0].state=='available'
assert ManualCondition.objects.get(listing=listing).choice=='good'
assert list(ListingEvent.objects.values_list('id','kind'))==baseline
assert ListingObservation.objects.filter(id=observation.id).exists()
print('known-interest listing absent in search recovered through owned detail boundary PASS')
""".replace("SOURCE_URL", repr(source_url)),
        )
    assert any(path == "/detail/11" for path, _ in source.calls)


def test_orphan_reconciliation_waits_for_owner_and_preserves_confirmed_versions(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
import os
repo=build_media_repository();store=build_media_store()
photo=gallery.photos[0];original=queries.file(UUID(a['listing']),photo.version_id,'original')
key=f"{a['listing']}/"+'f'*64
orphan=store._path(key);orphan.write_bytes(b'crash-before-db-commit')
os.utime(orphan,(0,0))
job=MediaJob.objects.filter(entry__capture_id=a['capture']).first()
job.state='running';job.lease_until=now()+timedelta(seconds=60);job.save()
assert repo.reconcile_orphans(store.reconcile_orphans,now())==0 and orphan.exists()
job.lease_until=now()-timedelta(seconds=1);job.save()
assert repo.reconcile_orphans(store.reconcile_orphans,now())>=1 and not orphan.exists()
assert store.read(original)
print('orphan reconciliation waits for lease and preserves confirmed originals PASS')
""",
    )


def test_lower_resolution_refresh_preserves_best_copy_and_backup_provenance(
    media_instance: tuple[FoundationInstance, str],
) -> None:
    instance, origin = media_instance
    shell(
        instance,
        origin,
        """
entry=MediaEntry.objects.get(capture_id=a['capture'],position=0)
asset=entry.asset;before=MediaAsset.objects.count()
entry.candidates=[dict(url=ORIGIN+'/primary-small.jpg',width=320,height=240)];entry.save()
job=MediaJob.objects.get(entry=entry,kind='download');job.state='pending';job.next_at=now();job.save()
runner.execute(job.id)
entry.refresh_from_db()
assert entry.asset_id==asset.id and entry.reason=='media_lower_quality_preserved'
assert MediaAsset.objects.count()==before
assert queries.gallery(UUID(a['listing']),UUID(a['observation'])).state=='partial'
assert queries.file(UUID(a['listing']),asset.id,'original').sha256==asset.sha256
repo=build_media_repository()
for pin in repo.protected_versions('lower-quality-backup',now()):repo.release(pin.reference_id,now())
print('lower resolution never downgrades original or leaves unbound backup assets PASS')
""",
    )
