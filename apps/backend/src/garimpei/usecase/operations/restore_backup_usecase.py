from uuid import UUID

from garimpei.domain.operations.ports import BackupRepository


class RestoreBackupUseCase:
    def __init__(self, repository: BackupRepository) -> None:
        self._repository = repository

    def execute(self, archive: str, *, isolated: bool) -> UUID:
        return self._repository.restore(archive, isolated=isolated)
