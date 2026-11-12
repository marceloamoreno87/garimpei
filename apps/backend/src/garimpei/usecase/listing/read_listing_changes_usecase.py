from garimpei.domain.listing.read_models import ChangePage, ChangesReader


class ReadListingChangesUseCase:
    def __init__(self, reader: ChangesReader) -> None:
        self._reader = reader

    def execute(self, after: int | None = None, limit: int = 100) -> ChangePage:
        if limit <= 0 or (after is not None and after < 0):
            raise ValueError("Expected a positive limit and nonnegative cursor")
        return self._reader.changes(after, limit)
