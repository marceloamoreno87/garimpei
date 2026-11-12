from garimpei.domain.listing.exploration import Criteria, ExplorationReader, OfferPage


class ReadOffersUseCase:
    def __init__(self, reader: ExplorationReader) -> None:
        self._reader = reader

    def execute(self, criteria: Criteria) -> OfferPage:
        return self._reader.page(criteria)
