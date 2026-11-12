from garimpei.domain.alert.alert import Binding, Outcome
from garimpei.domain.alert.ports import AlertStore, Messaging
from garimpei.domain.valuation.ports import Clock


class ReconcileAlertUseCase:
    def __init__(
        self, store: AlertStore, gateway: Messaging, binding: Binding | None, clock: Clock
    ) -> None:
        self._store, self._gateway, self._binding, self._clock = store, gateway, binding, clock

    def execute(self) -> None:
        binding = self._binding
        for identity in self._store.ready(self._clock(), reconcile=True):
            delivery = self._store.claim(identity, binding, self._clock(), reconcile=True)
            if delivery is not None:
                result = (
                    self._gateway.reconcile(delivery, self._clock())
                    if self._gateway.check(delivery.binding)
                    else (Outcome("uncertain", "session_unavailable"))
                )
                self._store.finish(delivery, result, self._clock())
