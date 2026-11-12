"""Restore interrupted media/F19 work without losing completed parts or prepared inputs."""

import json
from pathlib import Path

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.media import serve_media
from tests.factories.runtime import pause_worker, prepare_instance, resume_worker
from tests.integration.test_collection import command, shell


def test_restore_requeues_inflight_media_and_analysis_with_exact_prepared_png(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    with (
        first_eligibility_scenario(source_dir) as (source, _, _, _),
        serve_media() as (origin, calls),
    ):
        with source.private_file.open("a") as file:
            file.write(
                f"GARIMPEI_BACKUP_DIR={tmp_path / 'backups'}\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_MEDIA_MAX_FILE_BYTES=1048576\nGARIMPEI_MEDIA_EVAL_ORIGIN={origin}\n"
            )
        group = pause_worker(source)
        target = prepare_instance(
            source.root, tmp_path, "f17_inflight_" + source.config.instance[-8:]
        )
        with target.private_file.open("a") as file:
            file.write(
                f"GARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERTS_ENABLED=false\nGARIMPEI_MEDIA_ROOT={tmp_path / 'restored-media'}\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_MEDIA_MAX_FILE_BYTES=1048576\nGARIMPEI_MEDIA_EVAL_ORIGIN={origin}\n"
            )
        command(target, "./scripts/init.sh", "--disposable")
        target_group = pause_worker(target)
        try:
            shell(
                source,
                f"ORIGIN={origin!r}\n"
                + """
import hashlib,io,json
from datetime import timedelta
from pathlib import Path
from PIL import Image
from django.utils.timezone import now
from garimpei.config.env import load_inference_settings,load_operations_settings
from garimpei.domain.inference.request import AnalysisInput,ImageReference
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.persistence.media_models import MediaCapture,MediaEntry,MediaJob
from garimpei.infra.persistence.inference_models import InferencePart
from garimpei.infra.persistence.operations_models import BackupRecord
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.main import build_media_repository,build_backup_repository
listing=Listing.objects.select_related('latest').get(external_id='16001')
capture=MediaCapture.objects.get(observation=listing.latest)
entry=MediaEntry.objects.create(capture=capture,photo_key='controlled-inflight',position=0,primary=True,candidates=[{'url':ORIGIN+'/primary-large.jpg','width':1280,'height':960}])
job=MediaJob.objects.create(entry=entry,kind='download',next_at=now(),attempts=1)
claim=build_media_repository().claim(job.id,now());assert claim and claim.attempts==2
other=Listing.objects.select_related('latest').get(external_id='16002')
old_capture=MediaCapture.objects.get(observation=other.latest)
old_capture.state='running';old_capture.complete=False;old_capture.save()
expired_entry=MediaEntry.objects.create(capture=old_capture,photo_key='controlled-exhausted',position=0,primary=True,candidates=[{'url':ORIGIN+'/primary-large.jpg','width':1280,'height':960}])
expired=MediaJob.objects.create(entry=expired_entry,kind='download',next_at=now()-timedelta(seconds=60),state='running',attempts=4,lease_generation=4,lease_until=now()-timedelta(seconds=1))
image=io.BytesIO();Image.new('RGB',(4,4),'green').save(image,format='PNG');raw=image.getvalue();digest=hashlib.sha256(raw).hexdigest()
directory=load_inference_settings().directory;directory.mkdir(parents=True,exist_ok=True);(directory/digest).write_bytes(raw)
value=AnalysisInput(listing.latest_id,listing.latest.ordinal,'Usado. Funciona perfeitamente.',(ImageReference('controlled-image',1,digest),))
repo=PostgresInferenceRepository(lambda:0,3)
ticket=repo.admit(value,'controlled-artifact',(PreparedPart('confirmed','Usado.'),PreparedPart('inflight','Funciona perfeitamente.'),PreparedPart('image','',image_id='controlled-image',image_hash=digest)))
first=repo.claim(now());assert first
confirmed={'findings':[],'unknowns':['confirmed before copy'],'limitations':[]}
assert repo.publish(first,confirmed,{'controlled':True},now())
second=repo.claim(now());assert second and second.part.key=='inflight'
r=build_backup_repository();backup=r.create();record=BackupRecord.objects.get(id=backup)
data={'archive':str(load_operations_settings().backup_dir/record.file_key),'media_job':str(job.id),'media_generation':claim.generation,'exhausted_media_job':str(expired.id),'request':str(ticket.request_id),'old_inference_generation':second.generation,'confirmed_part':first.part_id,'running_part':second.part_id,'image_hash':digest,'image_sha256':hashlib.sha256(raw).hexdigest()}
(load_operations_settings().backup_dir/'inflight.json').write_text(json.dumps(data))
""",
            )
            data = json.loads((tmp_path / "backups/inflight.json").read_text())
            shell(
                target,
                f"DATA={data!r}\n"
                + """
import hashlib,json
from uuid import UUID
from django.utils.timezone import now
from garimpei.config.env import load_inference_settings
from garimpei.domain.inference.ports import PreparedPart,AnalysisWork
from garimpei.domain.inference.request import AnalysisInput
from garimpei.infra.persistence.media_models import MediaJob,MediaAsset,MediaCapture
from garimpei.infra.persistence.inference_models import InferenceControl,InferenceRequest,InferencePart
from garimpei.infra.repository.inference.postgres_repository import PostgresInferenceRepository
from garimpei.usecase.inference.run_analysis_usecase import RunAnalysisUseCase
from garimpei.main import build_backup_repository,build_media_repository,build_media_runner
r=build_backup_repository();r.restore(DATA['archive'],isolated=True)
job=MediaJob.objects.get(id=DATA['media_job'])
assert job.state=='pending' and job.lease_until is None and job.reserved_bytes==0
assert job.attempts==2 and job.lease_generation==DATA['media_generation']
expired=MediaJob.objects.select_related('entry__capture').get(id=DATA['exhausted_media_job'])
assert expired.state=='failed' and expired.reason=='media_retry_exhausted' and expired.attempts==4
assert expired.lease_generation==4 and expired.lease_until is None and expired.reserved_bytes==0
assert expired.entry.capture.state=='failed' and not expired.entry.capture.complete
assert expired.id not in build_media_repository().due(now())
build_media_runner().execute(expired.id)
assert job.id in build_media_repository().due(now())
for _ in range(3):
 for identity in build_media_repository().due(now()):build_media_runner().execute(identity)
job.refresh_from_db();assert job.state=='done' and job.lease_generation>DATA['media_generation'] and job.attempts==3
assert MediaAsset.objects.filter(state='available',thumbnail_state='ready').exists()
request=InferenceRequest.objects.get(id=DATA['request'])
assert request.state=='pending'
confirmed=InferencePart.objects.get(pk=DATA['confirmed_part']);before=confirmed.result.copy();before_metrics=confirmed.metrics.copy()
pending=InferencePart.objects.get(pk=DATA['running_part'])
assert pending.state=='pending' and pending.attempts==1 and pending.generation==DATA['old_inference_generation']
control=InferenceControl.objects.get(pk=1)
assert control.paused and control.active_request is None and control.generation>DATA['old_inference_generation']
directory=load_inference_settings().directory
assert hashlib.sha256((directory/DATA['image_hash']).read_bytes()).hexdigest()==DATA['image_sha256']
repo=PostgresInferenceRepository(lambda:0,3);assert repo.claim(now()) is None
repo.control(False,control.revision)
class RestoredAnalysisFake:
 def __init__(self):self.calls=[]
 def infer(self,part,artifact):
  self.calls.append(part.key)
  if part.key=='inflight':
   obsolete=AnalysisWork(UUID(DATA['request']),DATA['old_inference_generation'],DATA['running_part'],artifact,part)
   assert repo.publish(obsolete,{}, {},now()) is False
  if part.image_hash:assert hashlib.sha256((directory/part.image_hash).read_bytes()).hexdigest()==part.image_hash
  return {'content':json.dumps({'findings':[],'unknowns':['controlled resumed result'],'limitations':[]}), 'metrics':{'controlled':True}}
fake=RestoredAnalysisFake();runner=RunAnalysisUseCase(repo,fake,now)
assert runner.execute() and runner.execute() and not runner.execute()
assert fake.calls==['inflight','image']
request.refresh_from_db();pending.refresh_from_db();confirmed.refresh_from_db()
assert request.state=='succeeded' and pending.attempts==2 and pending.generation>DATA['old_inference_generation']
assert confirmed.result==before and confirmed.metrics==before_metrics and confirmed.attempts==1
# A consumed third attempt remains exhausted after recovery; no fourth automatic call.
from garimpei.infra.persistence.listing_models import Listing
from garimpei.infra.repository.operations.restore_gateway import _reset_inference_work
listing=Listing.objects.select_related('latest').get(external_id='16001')
other=repo.admit(AnalysisInput(listing.latest_id,listing.latest.ordinal,'Controlled exhausted input',()),'controlled-artifact',(PreparedPart('exhausted','Controlled exhausted input'),))
active=repo.claim(now());assert active and active.request_id==other.request_id
InferencePart.objects.filter(pk=active.part_id).update(attempts=3)
_reset_inference_work()
part=InferencePart.objects.get(pk=active.part_id)
assert part.state=='failed' and part.attempts==3
assert InferenceRequest.objects.get(id=other.request_id).state=='failed'
control=InferenceControl.objects.get(pk=1);repo.control(False,control.revision)
assert repo.claim(now()) is None
""",
            )
            assert (
                len(calls) == 1
            )  # Only the restored original is downloaded; thumbnail is derived.
            shell(
                source,
                f"from garimpei.infra.persistence.media_models import MediaJob;from garimpei.infra.persistence.inference_models import InferenceRequest;assert MediaJob.objects.get(id={data['media_job']!r}).state=='running';assert InferenceRequest.objects.get(id={data['request']!r}).state=='running'",
            )
        finally:
            resume_worker(target_group)
            command(target, "./scripts/stop.sh", "--clean")
            resume_worker(group)
