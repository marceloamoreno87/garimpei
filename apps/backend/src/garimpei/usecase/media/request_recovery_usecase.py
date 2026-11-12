from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from garimpei.domain.media.ports import MediaRepository


class RequestMediaRecoveryUseCase:
    def __init__(self, repository: MediaRepository, clock: Callable[[], datetime]) -> None:
        self._repository, self._clock = repository, clock

    def execute(self, listing_id: UUID, capture_id: UUID, revision: int) -> None:
        self._repository.retry(listing_id, capture_id, revision, self._clock())
