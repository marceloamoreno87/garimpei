from typing import Protocol
from uuid import UUID

from garimpei.domain.operations.download import ArchiveDownload


class OperationalQueries(Protocol):
    def read(self, interest: str | None = None) -> dict[str, object]: ...


class OperationalRepository(Protocol):
    def resume(self, identity: UUID, stage: str, revision: int) -> None: ...


class BackupRepository(Protocol):
    def download(self, identity: UUID) -> "ArchiveDownload": ...
    def create(self, *, only_due: bool = False) -> UUID | None: ...
    def export(self, identity: UUID, request_id: UUID) -> UUID: ...
    def catalog(self) -> dict[str, object]: ...
    def restore(self, archive: str, *, isolated: bool) -> UUID: ...
    def verify(self, identity: UUID) -> dict[str, object]: ...


class ProgressRecorder(Protocol):
    def confirm(
        self,
        stage: str,
        key: str,
        revision: int,
        boundary: str,
        now: "datetime",
        *,
        pending: int = 0,
    ) -> None: ...
    def failure(
        self,
        stage: str,
        key: str,
        revision: int,
        reason: str,
        now: "datetime",
        *,
        retry_after: int = 0,
    ) -> None: ...
    def admits(self, stage: str, key: str, revision: int, now: "datetime") -> bool: ...


from datetime import datetime  # noqa: E402
