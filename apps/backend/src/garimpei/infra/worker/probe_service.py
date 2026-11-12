import time
import uuid

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from garimpei.config.env import RuntimeConfig
from garimpei.infra.persistence.models import RuntimeProbe, RuntimeState
from garimpei.main import defer_runtime_probe, register_tasks


def begin_run(config: RuntimeConfig, run_id: str) -> None:
    register_tasks()
    with transaction.atomic():
        RuntimeState.objects.update_or_create(
            environment_id=config.environment_id,
            defaults={
                "run_id": uuid.UUID(run_id),
                "started_at": timezone.now(),
                "stopped_at": None,
                "last_probe_at": None,
                "probe_sequence": 0,
            },
        )
        probe = RuntimeProbe.objects.create(
            environment_id=config.environment_id, run_id=run_id, kind="control", sequence=0
        )
        defer_runtime_probe(str(probe.id))


def end_run(config: RuntimeConfig) -> None:
    RuntimeState.objects.filter(
        environment_id=config.environment_id, stopped_at__isnull=True
    ).update(stopped_at=timezone.now())


def enqueue_manual(config: RuntimeConfig) -> RuntimeProbe:
    register_tasks()
    with transaction.atomic():
        state = RuntimeState.objects.select_for_update().get(environment_id=config.environment_id)
        last = RuntimeProbe.objects.filter(
            environment_id=config.environment_id, run_id=state.run_id, kind="manual"
        ).aggregate(value=Max("sequence"))["value"]
        probe = RuntimeProbe.objects.create(
            environment_id=config.environment_id,
            run_id=state.run_id,
            kind="manual",
            sequence=0 if last is None else last + 1,
        )
        defer_runtime_probe(str(probe.id))
    return probe


def wait_probe(probe: RuntimeProbe, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if RuntimeProbe.objects.filter(id=probe.id, completed_at__isnull=False).exists():
            return True
        time.sleep(0.1)
    return False
