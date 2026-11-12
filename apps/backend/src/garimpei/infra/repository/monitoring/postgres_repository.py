from uuid import UUID

from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration as Row
from garimpei.infra.persistence.monitoring_models import MonitoringInterest
from garimpei.infra.repository.monitoring.mapper import restore


class PostgresMonitoringRepository:
    def find_by_id(self, identity: UUID) -> MonitoringConfiguration | None:
        row = Row.objects.select_for_update().filter(id=identity).first()
        return restore(row) if row else None

    def find_by_slot(self, slot: str) -> MonitoringConfiguration | None:
        row = Row.objects.select_for_update().filter(slot=slot).first()
        return restore(row) if row else None

    def find_current(self) -> MonitoringConfiguration | None:
        row = Row.objects.select_for_update().order_by("slot").first()
        return restore(row) if row else None

    def save(self, configuration: MonitoringConfiguration) -> None:
        if self.find_by_id(configuration.id) == configuration:
            return
        Row.objects.update_or_create(
            id=configuration.id,
            defaults={
                "slot": configuration.slot,
                "revision": configuration.revision,
                "cep": configuration.cep,
                "shipping_estimate": configuration.shipping_estimate,
                "resale_fee_percent": configuration.resale_fee_percent,
                "completed_at": configuration.completed_at,
                "completion_revision": configuration.completion_revision,
            },
        )
        MonitoringInterest.objects.filter(configuration_id=configuration.id).delete()
        MonitoringInterest.objects.bulk_create(
            [
                MonitoringInterest(
                    configuration_id=configuration.id,
                    kind=item.kind,
                    key=item.key,
                    label=item.label,
                )
                for item in configuration.interests
            ]
        )

    def delete(self, identity: UUID) -> None:
        Row.objects.filter(id=identity).delete()
