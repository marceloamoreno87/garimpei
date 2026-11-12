from uuid import UUID

from garimpei.domain.operations.ports import BackupRepository


class CreateBackupUseCase:
    def __init__(self, repository: BackupRepository) -> None:
        self._repository = repository

    def execute(self, *, only_due: bool = False) -> UUID | None:
        return self._repository.create(only_due=only_due)
