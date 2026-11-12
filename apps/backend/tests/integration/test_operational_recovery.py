from collections.abc import Iterator

import pytest

from tests.factories.first_eligibility import first_eligibility_scenario
from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker
from tests.integration.test_collection import shell


@pytest.fixture(scope="module")
def operational_instance(tmp_path_factory: pytest.TempPathFactory) -> Iterator[FoundationInstance]:
    private = tmp_path_factory.mktemp("operational-recovery")
    with first_eligibility_scenario(private) as (instance, _, _, _):
        with instance.private_file.open("a") as output:
            output.write(f"GARIMPEI_BACKUP_DIR={private / 'backups'}\n")
        group = pause_worker(instance)
        try:
            yield instance
        finally:
            resume_worker(group)


def test_same_boundary_does_not_reset_persisted_failure_budget(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from datetime import timedelta
from django.utils.timezone import now
from garimpei.config.env import load_config
from garimpei.infra.repository.operations.progress_repository import PostgresOperationalRepository
from garimpei.infra.persistence.operations_models import OperationalUnit
from garimpei.domain.operations.errors import OperationsError
stamp=now();identity=load_config().environment_id
store=PostgresOperationalRepository(identity,lambda:stamp)
store.confirm('listing','durable-budget',3,'A',stamp)
store.failure('listing','durable-budget',3,'source_transport',stamp)
store.failure('listing','durable-budget',3,'source_transport',stamp)
store.confirm('listing','durable-budget',3,'A',stamp+timedelta(seconds=200))
store.failure('listing','durable-budget',3,'source_transport',stamp)
row=OperationalUnit.objects.get(installation=identity,scope='durable-budget')
assert row.suspended and row.failures==3 and row.pending==1 and row.checkpoint=='A'
assert row.last_progress_at==stamp
assert not PostgresOperationalRepository(identity,lambda:stamp).admits('listing','durable-budget',3,stamp+timedelta(days=1))
try:store.resume(row.id,'listing',2)
except OperationsError:pass
else:raise AssertionError('obsolete revision resumed')
store.resume(row.id,'listing',3)
row.refresh_from_db();assert row.failures==0 and row.checkpoint=='A' and row.generation==1
""",
    )


def test_full_queue_repeated_admission_preserves_request_and_does_not_duplicate(
    operational_instance: FoundationInstance,
) -> None:
    with operational_instance.private_file.open("a") as output:
        output.write("GARIMPEI_OPERATIONS_ENABLED=true\n")
    shell(
        operational_instance,
        """
from uuid import uuid4
from django.db import connection,transaction
from garimpei.config.env import load_config
from garimpei.main import _enqueue
from garimpei.infra.persistence.operations_models import OperationalUnit
identity=load_config().environment_id
with connection.cursor() as cursor:
 cursor.execute("DELETE FROM procrastinate_jobs WHERE queue_name='valuation' AND status='todo'")
 cursor.execute("INSERT INTO procrastinate_jobs(task_name,args,queue_name,status) SELECT 'garimpei.evaluate_valuation',%s::jsonb,'valuation','todo' FROM generate_series(1,1000)",['{"work_id":"00000000-0000-4000-8000-000000000017"}'])
for _ in range(2):
 with transaction.atomic():assert _enqueue('garimpei.evaluate_valuation','valuation',0,work_id=str(uuid4()))==0
with connection.cursor() as cursor:
 cursor.execute("SELECT count(*) FROM procrastinate_jobs WHERE queue_name='valuation' AND status='todo'")
 assert cursor.fetchone()[0]==1000
row=OperationalUnit.objects.get(installation=identity,stage='valuation',revision=0)
assert row.suspended and row.reason=='queue_full' and row.pending==1000
with connection.cursor() as cursor:cursor.execute("DELETE FROM procrastinate_jobs WHERE queue_name='valuation' AND status='todo'")
work=str(uuid4())
with transaction.atomic():first=_enqueue('garimpei.evaluate_valuation','valuation',0,work_id=work)
assert first>0
with transaction.atomic():assert _enqueue('garimpei.evaluate_valuation','valuation',0,work_id=work)==first
row.refresh_from_db();assert not row.suspended and row.pending==0
with connection.cursor() as cursor:cursor.execute("DELETE FROM procrastinate_jobs WHERE queue_name='valuation' AND status='todo'")
""",
    )


def test_running_turn_allows_one_durable_successor_without_duplicate_requests(
    operational_instance: FoundationInstance,
) -> None:
    shell(
        operational_instance,
        """
from uuid import uuid4
from django.db import connection
from garimpei.main import _enqueue
arguments={'cycle_id':str(uuid4()),'generation':7}
first=_enqueue('garimpei.collect_listings','listing',0,**arguments)
with connection.cursor() as cursor:cursor.execute("UPDATE procrastinate_jobs SET status='doing' WHERE id=%s",[first])
assert _enqueue('garimpei.collect_listings','listing',0,**arguments)==first
successor=_enqueue('garimpei.collect_listings','listing',0,_continuation=True,**arguments)
assert successor and successor!=first
assert _enqueue('garimpei.collect_listings','listing',0,_continuation=True,**arguments)==successor
with connection.cursor() as cursor:
 cursor.execute("SELECT status,count(*) FROM procrastinate_jobs WHERE id=ANY(%s) GROUP BY status",[[first,successor]])
 assert dict(cursor.fetchall())=={'doing':1,'todo':1}
 cursor.execute("DELETE FROM procrastinate_jobs WHERE id=ANY(%s)",[[first,successor]])
""",
    )
