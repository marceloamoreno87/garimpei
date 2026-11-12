from garimpei.domain.monitoring.ports import MonitoringQueries
from garimpei.domain.monitoring.snapshot import MonitoringSnapshot


class ReadMonitoringConfigurationUseCase:
    def __init__(self, queries: MonitoringQueries) -> None:
        self._queries = queries

    def execute(self) -> MonitoringSnapshot:
        return self._queries.read_confirmed()
