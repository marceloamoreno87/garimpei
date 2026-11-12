from garimpei.domain.monitoring.errors import ConfigurationConflict
from garimpei.domain.monitoring.ports import CatalogGateway, MonitoringTransaction
from garimpei.usecase.monitoring.interests import resolve_interests
from garimpei.usecase.monitoring.save_step_usecase import StepInput


class UpdateMonitoringConfigurationUseCase:
    def __init__(self, transaction: MonitoringTransaction, catalog: CatalogGateway) -> None:
        self._transaction = transaction
        self._catalog = catalog

    def execute(self, data: StepInput) -> None:
        with self._transaction() as repository:
            active = repository.find_by_slot("active")
            if active is None:
                raise ConfigurationConflict()
            interests = resolve_interests(
                self._catalog, data.category_ids, data.product_names, active.interests
            )
            updated = active.update(
                data.cep, data.shipping_estimate, data.resale_fee_percent, interests, data.revision
            )
            repository.save(updated)
