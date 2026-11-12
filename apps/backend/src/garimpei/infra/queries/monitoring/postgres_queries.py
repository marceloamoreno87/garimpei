from django.db import DatabaseError, connection, transaction

from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.errors import ConfigurationReadFailed
from garimpei.domain.monitoring.ports import MonitoringRepository
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration as Row
from garimpei.infra.repository.monitoring.mapper import restore


class PostgresMonitoringQueries:
    def __init__(
        self, repository: MonitoringRepository, *, repeatable_snapshot: bool = False
    ) -> None:
        self._repository = repository
        self._repeatable_snapshot = repeatable_snapshot

    def read_confirmed(self) -> MonitoringSnapshot:
        active = self._read("active")
        if active is None:
            return MonitoringSnapshot()
        return MonitoringSnapshot(
            configured=True,
            configuration_id=active.id,
            revision=active.revision,
            completed_at=active.completed_at,
            cep=active.cep,
            shipping_estimate=active.shipping_estimate,
            resale_fee_percent=active.resale_fee_percent,
            category_ids=tuple(x.key for x in active.interests if x.kind == "category"),
            product_names=tuple(x.label for x in active.interests if x.kind == "product"),
        )

    def read_form(self) -> MonitoringConfiguration | None:
        # Lock the parent while reading its children, so a snapshot never mixes revisions.
        try:
            with transaction.atomic():
                return self._repository.find_current()
        except DatabaseError as error:
            raise ConfigurationReadFailed() from error

    def _read(self, slot: str) -> MonitoringConfiguration | None:
        try:
            if self._repeatable_snapshot:
                return self._read_snapshot(slot)
            with transaction.atomic():
                return self._repository.find_by_slot(slot)
        except DatabaseError as error:
            raise ConfigurationReadFailed() from error

    @staticmethod
    def _read_snapshot(slot: str) -> MonitoringConfiguration | None:
        # Parent and children share the caller's MVCC snapshot. A row lock here
        # would survive until the caller finishes compiling the entire F08 view.
        if not connection.in_atomic_block:
            raise DatabaseError(
                "Configuration snapshot: expected an outer repeatable-read transaction"
            )
        with connection.cursor() as cursor:
            cursor.execute("SHOW transaction_isolation")
            isolation = cursor.fetchone()[0]
        if isolation not in {"repeatable read", "serializable"}:
            raise DatabaseError(
                f"Configuration snapshot isolation {isolation!r}: expected repeatable read or serializable"
            )
        row = Row.objects.filter(slot=slot).first()
        return restore(row) if row else None
