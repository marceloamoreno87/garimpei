from uuid import UUID

from garimpei.domain.operations.ports import BackupRepository


class ExportBackupUseCase:
    def __init__(self, repository: BackupRepository) -> None:
        self._repository = repository

    def execute(self, identity: UUID, request_id: UUID) -> UUID:
        return self._repository.export(identity, request_id)
