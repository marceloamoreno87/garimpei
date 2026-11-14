"""Filled legacy migrations preserve signatures/cohorts and backfill real target metadata."""

from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest

from tests.factories.runtime import (
    FoundationInstance,
    pause_worker,
    prepare_instance,
    resume_worker,
)


@pytest.fixture
def migration_instance(tmp_path: Path) -> Iterator[FoundationInstance]:
    instance = prepare_instance(
        Path(__file__).resolve().parents[4], tmp_path, "f23_migration_" + uuid4().hex[:8]
    )
    started = instance.command("./scripts/init.sh", "--disposable")
    assert started.returncode == 0, started.stdout + started.stderr
    try:
        yield instance
    finally:
        stopped = instance.command("./scripts/stop.sh", "--clean")
        assert stopped.returncode == 0, stopped.stdout + stopped.stderr


def test_filled_legacy_profiles_migrate_and_rollback_without_resigning_cache(
    migration_instance: FoundationInstance,
) -> None:
    group = pause_worker(migration_instance)
    try:
        result = migration_instance.shell("""
from uuid import uuid4
from django.db import connection,transaction,IntegrityError
from django.db.migrations.executor import MigrationExecutor
from django.utils.timezone import now
from garimpei.infra.persistence.management.commands.local_ai import _smoke_observation
observation_id,_=_smoke_observation('F23-filled-migration','text')
executor=MigrationExecutor(connection)
executor.migrate([('runtime','0027_gold_qualification')])
old=executor.loader.project_state([('runtime','0027_gold_qualification')]).apps.get_model('runtime','InferenceRequest')
cohort=uuid4(); identities=[]
for index,profile in enumerate(['local-evidence-v1','condition-evidence-v1','condition-evidence-v4']):
 row=old.objects.create(observation_id=observation_id,revision=1,signature=str(index+1)*64,
  artifact='original-artifact',prompt_version=profile,schema_version=profile,created_at=now(),state='succeeded',
  cohort_id=cohort if index else None,cohort_generation=7 if index else None)
 identities.append((row.id,row.signature,row.cohort_id,row.cohort_generation))
executor=MigrationExecutor(connection);latest=executor.loader.graph.leaf_nodes('runtime');executor.migrate(latest)
from garimpei.infra.persistence.inference_models import InferenceRequest
for identity,signature,old_cohort,generation in identities:
 row=InferenceRequest.objects.get(pk=identity)
 assert row.signature==signature and row.cohort_id==old_cohort and row.cohort_generation==generation
 assert row.observation_id==observation_id and row.target_kind=='listing_observation'
 assert row.target_id==observation_id and row.target_revision==1,'legacy targets were not backfilled'
new=InferenceRequest.objects.create(observation_id=observation_id,revision=1,signature='f'*64,
 artifact='original-artifact',prompt_version='local-evidence-v1',schema_version='local-evidence-v1',created_at=now())
new.refresh_from_db();assert new.target_id==observation_id and new.target_revision==1
try:
 with transaction.atomic():
  InferenceRequest.objects.create(observation_id=observation_id,revision=1,signature='e'*64,
   artifact='original-artifact',prompt_version='local-evidence-v1',schema_version='local-evidence-v1',created_at=now(),target_id=uuid4(),target_revision=1)
 raise AssertionError('divergent supplied metadata was overwritten or accepted')
except IntegrityError:pass
executor=MigrationExecutor(connection);executor.migrate([('runtime','0029_assistance_reviews')])
for identity,signature,old_cohort,generation in identities:
 row=InferenceRequest.objects.get(pk=identity)
 assert row.target_id is None and row.target_revision is None
 assert (row.signature,row.cohort_id,row.cohort_generation)==(signature,old_cohort,generation)
executor=MigrationExecutor(connection);executor.migrate(executor.loader.graph.leaf_nodes('runtime'))
print('filled migration and rollback preserved three legacy profiles, signatures, observations and cohorts; old writer accepted, divergent target rejected')
""")
        assert result.returncode == 0, result.stdout + result.stderr
    finally:
        resume_worker(group)
