from uuid import UUID

from garimpei.domain.operations.ports import OperationalRepository


class ResumeStageUseCase:
    def __init__(self, repository: OperationalRepository) -> None:
        self._repository = repository

    def execute(self, identity: UUID, stage: str, revision: int) -> None:
        self._repository.resume(identity, stage, revision)
