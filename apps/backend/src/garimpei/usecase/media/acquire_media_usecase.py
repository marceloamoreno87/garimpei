from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from garimpei.domain.media.media import AnalysisMedia
from garimpei.domain.media.ports import MediaRepository


class AcquireMediaForAnalysisUseCase:
    def __init__(self, repository: MediaRepository, clock: Callable[[], datetime]) -> None:
        self._repository, self._clock = repository, clock

    def execute(
        self,
        listing_id: UUID,
        observation_id: UUID,
        version_id: UUID,
        consumer: str,
        execution: str,
    ) -> AnalysisMedia:
        return self._repository.acquire(
            listing_id, observation_id, version_id, consumer, execution, self._clock()
        )
