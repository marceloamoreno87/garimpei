from uuid import UUID

from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.read_models import ListingReader, ListingView
from garimpei.domain.listing.scope import Scope


class ReadListingUseCase:
    def __init__(self, reader: ListingReader, configuration: ConfigurationReader) -> None:
        self._reader = reader
        self._configuration = configuration

    def execute(self, listing_id: UUID) -> ListingView | None:
        return self._reader.listing(listing_id, Scope.from_snapshot(self._configuration.execute()))
