from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


class GoldDiagnosticReadFailed(Exception):
    pass


@dataclass(frozen=True)
class GoldDiagnostic:
    state: str
    reason: str
    reasons: tuple[str, ...]
    label: str
    canonical_name: str
    product_key: str
    policy: str
    evaluated_at: datetime
    observation_id: UUID
    current: bool
    retained_count: int
    method: str
    valid_until: datetime | None
    evidence: dict[str, object]


class GoldDiagnosticQueries(Protocol):
    def read(self, listing_id: UUID) -> GoldDiagnostic | None: ...
