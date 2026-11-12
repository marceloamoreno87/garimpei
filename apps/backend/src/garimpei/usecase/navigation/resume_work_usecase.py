from uuid import UUID

from garimpei.domain.navigation.ports import NavigationStore


class ResumeWorkUseCase:
    def __init__(self, repository: NavigationStore) -> None:
        self._repository = repository

    def execute(self, work_id: UUID, revision: int) -> None:
        self._repository.resume(work_id, revision)
