from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from garimpei.domain.valuation.profit import ProfitComposition

type ReevaluationCause = Literal["automatic_input", "identity_correction", "adoption"]


class FirstAlertStore(Protocol):
    def adopt(self, now: datetime) -> None: ...
    def pending(self, now: datetime) -> tuple[UUID, ...]: ...
    def prepare(self, identity: UUID) -> str: ...
    def publish(
        self,
        identity: UUID,
        signature: str,
        profit: ProfitComposition | None,
        now: datetime,
        *,
        cause: ReevaluationCause = "automatic_input",
    ) -> None: ...
    def defer(self, identity: UUID, now: datetime) -> None: ...
