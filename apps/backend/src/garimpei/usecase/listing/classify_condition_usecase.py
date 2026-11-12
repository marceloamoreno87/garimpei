from uuid import UUID

from garimpei.domain.listing.condition import Choice
from garimpei.domain.listing.condition_ports import ConditionRepository


class ClassifyConditionUseCase:
    def __init__(self, repository: ConditionRepository) -> None:
        self._repository = repository

    def execute(self, identity: UUID, choice: Choice, revision: int) -> int:
        return self._repository.save(identity, choice, revision)
