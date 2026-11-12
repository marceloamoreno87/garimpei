from dataclasses import dataclass

from garimpei.domain.monitoring.ports import MonitoringFormQueries
from garimpei.domain.monitoring.values import Interest


@dataclass(frozen=True)
class MonitoringForm:
    slot: str = "draft"
    revision: int = 0
    next_step: str = "regiao"
    cep: str = ""
    shipping_estimate: str = ""
    resale_fee_percent: str = ""
    interests: tuple[Interest, ...] = ()


class ReadMonitoringFormUseCase:
    def __init__(self, queries: MonitoringFormQueries) -> None:
        self._queries = queries

    def execute(self) -> MonitoringForm:
        config = self._queries.read_form()
        if config is None:
            return MonitoringForm()
        return MonitoringForm(
            slot=config.slot,
            revision=config.revision,
            next_step=config.next_step,
            cep=f"{config.cep[:5]}-{config.cep[5:]}" if config.cep else "",
            shipping_estimate=str(config.shipping_estimate)
            if config.shipping_estimate is not None
            else "",
            resale_fee_percent=str(config.resale_fee_percent)
            if config.resale_fee_percent is not None
            else "",
            interests=config.interests,
        )
