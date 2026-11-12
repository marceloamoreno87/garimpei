from datetime import datetime
from typing import Protocol
from uuid import UUID

from garimpei.domain.valuation.profit import ProfitInput


class ProfitReadFailed(Exception):
    code = "PROFIT_DEPENDENCY_UNAVAILABLE"
    retryable = True

    def __init__(self) -> None:
        super().__init__("Não foi possível consultar os dados do lucro. Tente novamente.")


class UnsupportedProfitEvent(ValueError):
    code = "UNSUPPORTED_PROFIT_EVENT"

    def __init__(self, kind: str) -> None:
        super().__init__(f"Evento {kind!r}; esperado discovered ou price_decreased.")


class ProfitReader(Protocol):
    def read(self, identity: UUID, now: datetime, *, event: bool) -> ProfitInput | None: ...
