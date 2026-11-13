from collections.abc import Iterator
from contextlib import contextmanager

from django.db import DatabaseError, connection, transaction

from garimpei.domain.monitoring.errors import ConfigurationSaveFailed
from garimpei.domain.monitoring.ports import MonitoringRepository
from garimpei.infra.repository.robot.locking import lock_robot_control


class PostgresMonitoringUnitOfWork:
    def __init__(self, repository: MonitoringRepository) -> None:
        self._repository = repository

    @contextmanager
    def transaction(self) -> Iterator[MonitoringRepository]:
        try:
            with transaction.atomic(durable=True):
                lock_monitoring_publication()
                yield self._repository
        except DatabaseError as error:
            raise ConfigurationSaveFailed() from error


def lock_monitoring_publication() -> None:
    lock_robot_control()
    # Row locks cannot serialize simultaneous first POSTs when no slot exists yet.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(73003)")
