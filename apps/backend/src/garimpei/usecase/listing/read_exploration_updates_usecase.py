from uuid import UUID

from garimpei.domain.listing.exploration import ExplorationReader


class ReadExplorationUpdatesUseCase:
    def __init__(self, reader: ExplorationReader) -> None:
        self._reader = reader

    def execute(self, version: UUID | None) -> tuple[bool, bool]:
        return self._reader.updates(version)
