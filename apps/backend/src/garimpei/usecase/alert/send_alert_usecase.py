from uuid import UUID

from garimpei.domain.alert.alert import Binding
from garimpei.domain.alert.ports import AlertStore, EventFeed, Messaging
from garimpei.domain.valuation.ports import Clock


class SendAlertUseCase:
    def __init__(
        self,
        store: AlertStore,
        gateway: Messaging,
        binding: Binding | None,
        feed: EventFeed,
        clock: Clock,
    ) -> None:
        self._store, self._gateway, self._binding = store, gateway, binding
        self._feed, self._clock = feed, clock

    def execute(self) -> None:
        # Read the durable feed before authorizing any external effect after recovery.
        try:
            self._feed.execute(self._store.cursor(), 1)
        except Exception:
            self._store.pause()
            raise
        for identity in self._store.ready(self._clock(), reconcile=False):
            self._send(identity)

    def _send(self, identity: UUID) -> None:
        binding = self._binding
        if binding is None:
            self._store.block(identity, "configuration_missing", self._clock())
            return
        ready = self._gateway.check(binding)
        if not ready:
            self._store.block(identity, "session_unavailable", self._clock())
            return
        delivery = (
            self._store.claim(identity, binding, self._clock(), reconcile=False) if ready else None
        )
        if delivery is not None:
            result = self._gateway.send(delivery)
            self._store.finish(delivery, result, self._clock())
