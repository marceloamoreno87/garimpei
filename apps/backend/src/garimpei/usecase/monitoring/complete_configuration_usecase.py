from dataclasses import replace

from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.errors import ConfigurationConflict
from garimpei.domain.monitoring.ports import CatalogGateway, MonitoringTransaction
from garimpei.usecase.monitoring.interests import resolve_interests
from garimpei.usecase.monitoring.save_step_usecase import StepInput


class CompleteMonitoringConfigurationUseCase:
    def __init__(self, transaction: MonitoringTransaction, catalog: CatalogGateway) -> None:
        self._transaction = transaction
        self._catalog = catalog

    def execute(self, data: StepInput) -> None:
        with self._transaction() as repository:
            active = repository.find_by_slot("active")
            draft = repository.find_by_slot("draft")
            if active is not None:
                self._check_replay(active, data)
                return
            draft = draft or MonitoringConfiguration.create()
            if data.revision != draft.revision:
                raise ConfigurationConflict()
            interests = resolve_interests(
                self._catalog, data.category_ids, data.product_names, draft.interests
            )
            updated = draft.save_interests(interests, data.revision)
            published = updated.publish(updated.revision)
            # Remember the submitted revision, including unsaved interests on the final screen.
            repository.save(replace(published, completion_revision=data.revision))

    def _check_replay(self, active: MonitoringConfiguration, data: StepInput) -> None:
        if data.revision != active.completion_revision:
            raise ConfigurationConflict()
        interests = resolve_interests(
            self._catalog, data.category_ids, data.product_names, active.interests
        )
        candidate = active.save_interests(interests, active.revision)
        if candidate != active:
            raise ConfigurationConflict()
