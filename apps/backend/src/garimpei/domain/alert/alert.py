from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from garimpei.domain.alert.financial_snapshot import FinancialSnapshot


@dataclass(frozen=True)
class Binding:
    session: str = field(repr=False)
    recipient: str = field(repr=False)
    account: str = field(repr=False)


@dataclass(frozen=True)
class AlertMessage:
    reference: UUID
    kind: str
    title: str
    source: str
    price: Decimal
    previous_price: Decimal | None
    profit: Decimal
    observed_at: datetime
    url: str
    profit_policy: str = "potential-before-freight-v2"
    financial: FinancialSnapshot | None = None


@dataclass(frozen=True)
class Receipt:
    id: str
    outgoing: bool
    chat: str = field(repr=False)
    body: str = field(repr=False)
    ack: int = 0


@dataclass(frozen=True)
class Delivery:
    reference: UUID
    generation: int
    binding: Binding
    body: str = field(repr=False)
    authorized_at: datetime
    message_id: str | None
    reconcile: bool
    attempt_id: UUID | None = None


@dataclass(frozen=True)
class Outcome:
    state: str
    reason: str
    receipt: Receipt | None = None
    retry_after: int = 0


@dataclass(frozen=True)
class AlertPolicy:
    tick: int = 5
    timeout: int = 10
    lease: int = 60
    retry_base: int = 15
    retry_max: int = 300
    window: int = 86400
    history_pages: int = 10
    history_limit: int = 100
    clock_margin: int = 300

    def delay(self, failures: int) -> int:
        return min(self.retry_max, self.retry_base * (1 << max(0, min(failures, 10))))
