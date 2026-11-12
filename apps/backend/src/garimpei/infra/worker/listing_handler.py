from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from garimpei.domain.listing.ports import Attempt


class CollectionRunner(Protocol):
    def execute(self, attempt: Attempt) -> None: ...


class ListingTaskHandler:
    def __init__(self, collect: CollectionRunner, close: Callable[[], None] | None = None) -> None:
        self._collect = collect
        self._close = close

    def execute(self, cycle_id: str, generation: int) -> None:
        try:
            self._collect.execute(Attempt(UUID(cycle_id), generation))
        finally:
            if self._close is not None:
                self._close()
