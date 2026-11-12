from garimpei.domain.alert.first_ports import FirstAlertStore
from garimpei.domain.valuation.ports import Clock


class AdoptFirstAlertsUseCase:
    def __init__(self, store: FirstAlertStore, clock: Clock) -> None:
        self._store, self._clock = store, clock

    def execute(self) -> None:
        self._store.adopt(self._clock())
