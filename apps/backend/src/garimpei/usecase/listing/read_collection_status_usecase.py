from garimpei.domain.listing.ports import ConfigurationReader
from garimpei.domain.listing.read_models import CollectionStatus, StatusReader
from garimpei.domain.listing.scope import Scope


class ReadCollectionStatusUseCase:
    def __init__(self, reader: StatusReader, configuration: ConfigurationReader) -> None:
        self._reader = reader
        self._configuration = configuration

    def execute(self) -> CollectionStatus:
        return self._reader.status(Scope.from_snapshot(self._configuration.execute()))
