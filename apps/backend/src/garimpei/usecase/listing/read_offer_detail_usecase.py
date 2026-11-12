from uuid import UUID

from garimpei.domain.listing.exploration import ExplorationReader, Offer


class ReadOfferDetailUseCase:
    def __init__(self, reader: ExplorationReader) -> None:
        self._reader = reader

    def execute(self, identity: UUID, version: UUID | None) -> tuple[Offer | None, UUID | None]:
        return self._reader.detail(identity, version)
