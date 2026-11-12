from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from garimpei.domain.listing.condition import Choice, ConditionState
from garimpei.domain.listing.listing import Evidence


@dataclass(frozen=True)
class ConditionView:
    id: UUID
    external_id: str
    source: str
    canonical_url: str
    title: str
    evidence: Evidence
    state: ConditionState
    observed_at: datetime
    price: Decimal | None
    visible: bool


class ConditionQueries(Protocol):
    def read(self, identity: UUID) -> ConditionView | None: ...
    def all_visible(self) -> tuple[ConditionView, ...]: ...


class ConditionRepository(Protocol):
    def save(self, identity: UUID, choice: Choice, revision: int) -> int: ...


class ConditionError(Exception):
    code = "CONDITION_UNAVAILABLE"
    status = 503


class ConditionNotFound(ConditionError):
    code = "CONDITION_NOT_FOUND"
    status = 404


class InvalidConditionInput(ConditionError):
    code = "INVALID_CONDITION_INPUT"
    status = 400


class ConditionConflict(ConditionError):
    code = "CONDITION_CONFLICT"
    status = 409


class ConditionSaveFailed(ConditionError):
    code = "CONDITION_SAVE_FAILED"
