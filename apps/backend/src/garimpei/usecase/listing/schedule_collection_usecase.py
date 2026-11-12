from garimpei.domain.listing.ports import CollectionPolicy, CollectionStore


class ScheduleCollectionUseCase:
    def __init__(self, store: CollectionStore, policy: CollectionPolicy) -> None:
        self._store = store
        self._policy = policy

    def execute(self) -> None:
        self._store.reconcile(self._policy)
