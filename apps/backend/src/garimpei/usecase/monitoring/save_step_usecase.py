from dataclasses import dataclass

from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.errors import ConfigurationConflict
from garimpei.domain.monitoring.ports import CatalogGateway, MonitoringTransaction
from garimpei.usecase.monitoring.interests import resolve_interests


@dataclass(frozen=True)
class StepInput:
    step: str
    revision: int
    cep: str = ""
    shipping_estimate: str = ""
    resale_fee_percent: str = ""
    category_ids: tuple[str, ...] = ()
    product_names: tuple[str, ...] = ()


class SaveMonitoringStepUseCase:
    def __init__(self, transaction: MonitoringTransaction, catalog: CatalogGateway) -> None:
        self._transaction = transaction
        self._catalog = catalog

    def execute(self, data: StepInput) -> None:
        with self._transaction() as repository:
            if repository.find_by_slot("active") is not None:
                raise ConfigurationConflict()
            draft = repository.find_by_slot("draft") or MonitoringConfiguration.create()
            updated = self._apply(draft, data)
            repository.save(updated)

    def _apply(self, draft: MonitoringConfiguration, data: StepInput) -> MonitoringConfiguration:
        if data.step == "regiao":
            return draft.save_region(data.cep, data.revision)
        if data.step == "custos":
            return draft.save_costs(data.shipping_estimate, data.resale_fee_percent, data.revision)
        interests = resolve_interests(
            self._catalog, data.category_ids, data.product_names, draft.interests
        )
        return draft.save_interests(interests, data.revision)
