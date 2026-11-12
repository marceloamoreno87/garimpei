from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from garimpei.domain.media.ports import MediaRepository


class ReleaseMediaReferenceUseCase:
    def __init__(self, repository: MediaRepository, clock: Callable[[], datetime]) -> None:
        self._repository, self._clock = repository, clock

    def execute(self, reference_id: UUID) -> None:
        self._repository.release(reference_id, self._clock())
