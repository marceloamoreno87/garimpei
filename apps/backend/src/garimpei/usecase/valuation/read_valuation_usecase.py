from uuid import UUID

from garimpei.domain.valuation.ports import Clock, ValuationReader
from garimpei.domain.valuation.values import Valuation


class ReadValuationUseCase:
    def __init__(self, reader: ValuationReader, clock: Clock) -> None:
        self._reader, self._clock = reader, clock

    def execute(self, identity: UUID, *, historical: bool = False) -> Valuation | None:
        if historical:
            return self._reader.historical(identity)
        return self._reader.current(identity, self._clock())
