from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Protocol
from uuid import UUID

from garimpei.domain.monitoring.configuration import MonitoringConfiguration
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot
from garimpei.domain.monitoring.values import CategoryCatalog


class MonitoringRepository(Protocol):
    def find_by_id(self, identity: UUID) -> MonitoringConfiguration | None: ...
    def find_by_slot(self, slot: str) -> MonitoringConfiguration | None: ...
    def find_current(self) -> MonitoringConfiguration | None: ...
    def save(self, configuration: MonitoringConfiguration) -> None: ...
    def delete(self, identity: UUID) -> None: ...


class MonitoringQueries(Protocol):
    def read_confirmed(self) -> MonitoringSnapshot: ...


class MonitoringFormQueries(Protocol):
    def read_form(self) -> MonitoringConfiguration | None: ...


class CatalogGateway(Protocol):
    def load(self) -> CategoryCatalog: ...


type MonitoringTransaction = Callable[[], AbstractContextManager[MonitoringRepository]]
