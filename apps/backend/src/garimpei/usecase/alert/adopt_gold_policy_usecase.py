from collections.abc import Callable
from datetime import datetime

from garimpei.domain.alert.gold_evidence import GoldPolicyRepository


class AdoptGoldPolicyUseCase:
    def __init__(self, repository: GoldPolicyRepository, clock: Callable[[], datetime]) -> None:
        self._repository, self._clock = repository, clock

    def execute(self) -> dict[str, object]:
        return self._repository.adopt(self._clock())
