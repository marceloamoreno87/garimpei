from garimpei.domain.alert.ports import AlertStore, EventFeed
from garimpei.domain.valuation.ports import Clock


class ConsumeListingEventsUseCase:
    def __init__(self, store: AlertStore, feed: EventFeed, clock: Clock) -> None:
        self._store, self._feed, self._clock = store, feed, clock

    def execute(self) -> None:
        try:
            page = self._feed.execute(self._store.cursor(), 100)
            self._store.ingest(page, self._clock())
        except Exception:
            self._store.pause()
            raise
