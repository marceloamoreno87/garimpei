from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.values import Interest
from garimpei.infra.persistence.monitoring_models import MonitoringConfiguration as Row
from garimpei.infra.persistence.monitoring_models import MonitoringInterest


def restore(row: Row) -> MonitoringConfiguration:
    interests = tuple(
        Interest(item.kind, item.key, item.label)
        for item in MonitoringInterest.objects.filter(configuration_id=row.id).order_by(
            "kind", "key"
        )
    )
    return MonitoringConfiguration(
        id=row.id,
        slot=row.slot,
        revision=row.revision,
        cep=row.cep,
        shipping_estimate=row.shipping_estimate,
        resale_fee_percent=row.resale_fee_percent,
        interests=interests,
        completed_at=row.completed_at,
        completion_revision=row.completion_revision,
    )
