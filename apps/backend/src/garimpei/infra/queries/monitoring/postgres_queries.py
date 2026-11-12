from django.db import DatabaseError, transaction

from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.errors import ConfigurationReadFailed
from garimpei.domain.monitoring.ports import MonitoringRepository
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot


class PostgresMonitoringQueries:
    def __init__(self, repository: MonitoringRepository) -> None:
        self._repository = repository

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
            with transaction.atomic():
                return self._repository.find_by_slot(slot)
        except DatabaseError as error:
            raise ConfigurationReadFailed() from error
