from collections.abc import Callable
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from garimpei.infra.persistence.models import RuntimeProbe, RuntimeState


class RuntimeTaskHandler:
    def __init__(self, defer: Callable[[str, int], int]) -> None:
        self._defer = defer

    def execute(self, probe_id: str) -> None:
        with transaction.atomic():
            probe = RuntimeProbe.objects.select_for_update().get(id=UUID(probe_id))
            if probe.completed_at is not None:
                return
            probe.completed_at = timezone.now()
            probe.save(update_fields=["completed_at"])
            if probe.kind == "control":
                self._continue(probe)

    def _continue(self, probe: RuntimeProbe) -> None:
        state = RuntimeState.objects.select_for_update().get(environment_id=probe.environment_id)
        if state.run_id != probe.run_id or state.stopped_at is not None:
            return
        state.last_probe_at = timezone.now()
        state.probe_sequence = probe.sequence + 1
        state.save(update_fields=["last_probe_at", "probe_sequence"])
        successor = RuntimeProbe.objects.create(
            environment_id=probe.environment_id,
            run_id=probe.run_id,
            kind="control",
            sequence=state.probe_sequence,
        )
        self._defer(str(successor.id), 5)
