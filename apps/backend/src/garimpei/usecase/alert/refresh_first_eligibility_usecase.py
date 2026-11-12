from garimpei.domain.alert.first_ports import FirstAlertStore
from garimpei.domain.alert.ports import ProfitQuery
from garimpei.domain.valuation.ports import Clock
from garimpei.domain.valuation.profit_queries import ProfitReadFailed


class RefreshFirstEligibilityUseCase:
    def __init__(self, store: FirstAlertStore, profit: ProfitQuery, clock: Clock) -> None:
        self._store, self._profit, self._clock = store, profit, clock

    def execute(self) -> None:
        for identity in self._store.pending(self._clock()):
            signature = self._store.prepare(identity)
            try:
                # F07 opens its own consistent read, outside the publication lock.
                result = self._profit.execute(identity, event=False)
            except ProfitReadFailed:
                self._store.defer(identity, self._clock())
                continue
            self._store.publish(identity, signature, result, self._clock())
