"""Protected originals and thumbnails survive real snapshot/export/isolated restore."""

from pathlib import Path

from tests.factories.media import prepare_media_instance, serve_media
from tests.factories.runtime import pause_worker, prepare_instance, resume_worker
from tests.integration.test_collection import command, shell
from tests.integration.test_media_persistence import BOOTSTRAP


def test_protected_media_pins_exact_files_missing_bytes_and_restore(tmp_path: Path) -> None:
    source_private = tmp_path / "source"
    source_private.mkdir()
    root = Path(__file__).resolve().parents[4]
    with serve_media() as (origin, _):
        source = prepare_media_instance(root, source_private, origin)
        with source.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_BACKUP_DIR={tmp_path / 'backups'}\nGARIMPEI_AI_SERVICE_ENABLED=false\n"
            )
        command(source, "./scripts/init.sh", "--disposable")
        group = pause_worker(source)
        target = prepare_instance(
            root, tmp_path, "f17_media_restore_" + source.config.instance[-8:]
        )
        with target.private_file.open("a") as output:
            output.write(
                f"GARIMPEI_BACKUP_DIR={tmp_path / 'restored-backups'}\nGARIMPEI_MEDIA_ROOT={tmp_path / 'restored-media'}\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERTS_ENABLED=false\n"
            )
        command(target, "./scripts/init.sh", "--disposable")
        target_group = pause_worker(target)
        try:
            shell(
                source,
                "ORIGIN="
                + repr(origin)
                + "\n"
                + BOOTSTRAP
                + """
import json
from pathlib import Path
from garimpei.main import build_backup_repository
from garimpei.config.env import load_operations_settings
from garimpei.infra.gateway.operations.archive_gateway import ArchiveGateway
from garimpei.infra.persistence.operations_models import BackupRecord
from garimpei.domain.operations.errors import OperationsError
settings=load_operations_settings(); r=build_backup_repository()
asset=MediaAsset.objects.get(id=gallery.photos[0].version_id)
entry=MediaEntry.objects.filter(asset=asset).first(); entry.candidates=[{'url':ORIGIN+'/primary-large.jpg?oh=synthetic-access-canary','width':1280,'height':960}];entry.save()
original=r._archives
class ObservePinsArchive(ArchiveGateway):
 def write(self,*args,**kwargs):
  assert MediaReference.objects.filter(consumer='backup',released_at=None).exists()
  Listing.objects.filter(id=asset.listing_id).update(media_tracking_active=False)
  CleanMediaUseCase(build_media_repository(),build_media_store(),now).execute()
  assert MediaAsset.objects.get(id=asset.id).state=='available'
  return super().write(*args,**kwargs)
r._archives=ObservePinsArchive(settings.backup_dir,owner=settings.environment_id)
identity=r.create(); assert identity
assert not MediaReference.objects.filter(consumer='backup',released_at=None).exists()
record=BackupRecord.objects.get(id=identity)
metadata,files=original.read(original.resolve(record.file_key))
assert metadata['protected_media']
assert any(name.startswith('media/') and name.endswith('/original') for name in files)
assert any(name.endswith('/thumbnail') for name in files)
assert b'synthetic-access-canary' not in b''.join(data for name,data in files.items() if name.endswith('.jsonl'))
selected=original.resolve(record.file_key); prior=selected.read_bytes()
Listing.objects.filter(id=asset.listing_id).update(media_tracking_active=True)
file=queries.file(asset.listing_id,asset.id,'original'); saved=build_media_store().read(file)
build_media_store()._path(file.key).unlink()
try:r.create()
except OperationsError:pass
else:raise AssertionError('missing required original accepted')
assert selected.read_bytes()==prior and BackupRecord.objects.get(id=identity).state=='completed'
build_media_store().restore(file,saved)
assert not MediaReference.objects.filter(consumer='backup',released_at=None).exists()
expected={item['id']:{'sha256':MediaAsset.objects.get(id=item['id']).sha256,'key':item['key']} for item in metadata['protected_media']}
(settings.backup_dir/'transfer.json').write_text(json.dumps({'archive':str(selected),'expected':expected}))
""",
            )
            import json

            transfer = json.loads((tmp_path / "backups/transfer.json").read_text())
            shell(
                target,
                f"""
import hashlib
from uuid import UUID
from django.test import Client
from garimpei.main import build_backup_repository,build_media_store,build_recovery_guard
from garimpei.infra.persistence.media_models import MediaAsset,MediaReference
from garimpei.infra.queries.media.postgres_queries import PostgresMediaQueries
r=build_backup_repository();r.restore({transfer["archive"]!r},isolated=True)
assert build_recovery_guard()()
expected={transfer["expected"]!r}; queries=PostgresMediaQueries()
for identity,value in expected.items():
 asset=MediaAsset.objects.get(id=identity)
 assert asset.sha256==value['sha256'] and asset.key==value['key']
 file=queries.file(asset.listing_id,asset.id,'original')
 assert hashlib.sha256(build_media_store().read(file)).hexdigest()==value['sha256']
 if asset.thumbnail_state=='ready':
  thumb=queries.file(asset.listing_id,asset.id,'miniatura')
  assert hashlib.sha256(build_media_store().read(thumb)).hexdigest()==asset.thumbnail_hash
 response=Client(HTTP_HOST='127.0.0.1').get(f'/ofertas/{{asset.listing_id}}/imagens/{{identity}}/original/')
 assert response.status_code==200 and hashlib.sha256(response.content).hexdigest()==value['sha256']
assert not MediaReference.objects.filter(consumer='backup',released_at=None).exists()
""",
            )
        finally:
            resume_worker(target_group)
            command(target, "./scripts/stop.sh", "--clean")
            resume_worker(group)
            command(source, "./scripts/stop.sh", "--clean")
