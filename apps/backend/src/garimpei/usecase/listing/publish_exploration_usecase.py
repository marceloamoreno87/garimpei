from uuid import UUID

from garimpei.domain.listing.exploration import ExplorationPublisher
from garimpei.domain.listing.ports import Clock


class PublishExplorationUseCase:
    def __init__(self, publisher: ExplorationPublisher, clock: Clock) -> None:
        self._publisher = publisher
        self._clock = clock

    def execute(self) -> UUID | None:
        return self._publisher.publish(self._clock())
