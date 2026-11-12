import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from django.db import connection

logger = logging.getLogger("garimpei.alert")
STAGES = {
    "ingest": 74001,
    "evaluate": 74002,
    "send": 74003,
    "reconcile": 74004,
    "adopt": 74005,
    "refresh": 74006,
}


@contextmanager
def _stage_lock(stage: str) -> Iterator[bool]:
    # A session lock releases when a killed worker's connection closes. A technical
    # job left 'doing' must never prevent the next business reconciliation.
    key = STAGES[stage]
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [key])
        acquired = bool(cursor.fetchone()[0])
    try:
        yield acquired
    finally:
        if acquired:
            _unlock(key)


def _unlock(key: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_unlock(%s)", [key])


class AlertTaskHandler:
    def __init__(self, stage: str, execute: Callable[[], None]) -> None:
        self._stage, self._execute = stage, execute

    def execute(self) -> None:
        try:
            self._run_stage()
        except Exception:
            logger.error(
                "alert_stage_failed",
                extra={"event": "alert_stage_failed", "error_code": "ALERT_DEPENDENCY_UNAVAILABLE"},
            )
            raise

    def _run_stage(self) -> None:
        with _stage_lock(self._stage) as acquired:
            if acquired:
                self._execute()
