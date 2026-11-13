from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from garimpei.domain.alert.gold_evidence import GoldDecision, GoldEvidenceRepository


class QualifyGoldAlertUseCase:
    def __init__(self, repository: GoldEvidenceRepository, clock: Callable[[], datetime]) -> None:
        self._repository, self._clock = repository, clock

    def execute(self, listing_id: UUID, purpose_key: str = "first") -> GoldDecision:
        return self._repository.qualify(listing_id, purpose_key, self._clock())
