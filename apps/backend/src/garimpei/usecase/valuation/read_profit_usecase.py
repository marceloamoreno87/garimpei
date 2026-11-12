from uuid import UUID

from garimpei.domain.valuation.ports import Clock
from garimpei.domain.valuation.profit import ProfitComposition, compose_profit
from garimpei.domain.valuation.profit_queries import ProfitReader


class ReadProfitUseCase:
    def __init__(self, reader: ProfitReader, clock: Clock) -> None:
        self._reader, self._clock = reader, clock

    def execute(self, identity: UUID, *, event: bool = False) -> ProfitComposition | None:
        now = self._clock()
        value = self._reader.read(identity, now, event=event)
        return compose_profit(value, now) if value else None
