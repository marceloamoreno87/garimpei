from garimpei.domain.alert.ports import AlertStore, ProfitQuery
from garimpei.domain.valuation.ports import Clock
from garimpei.domain.valuation.profit_queries import ProfitReadFailed


class EvaluateAlertUseCase:
    def __init__(self, store: AlertStore, profit: ProfitQuery, clock: Clock) -> None:
        self._store, self._profit, self._clock = store, profit, clock

    def execute(self) -> None:
        for identity in self._store.pending(self._clock()):
            try:
                result = self._profit.execute(identity, event=True)
            except ProfitReadFailed:
                self._store.defer_evaluation(identity, self._clock())
                continue
            self._store.evaluate(identity, result, self._clock())
