from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from garimpei.domain.valuation.identification_values import IdentificationResult


@dataclass(frozen=True)
class IdentityEdit:
    listing_id: UUID
    observed_revision: int
    manual_revision: int
    action: Literal["save", "resolve"]
    values: tuple[tuple[str, str], ...] = ()
    resolution: Literal["keep_manual", "use_observed", "correct"] | None = None


@dataclass(frozen=True)
class IdentityView:
    listing_id: UUID
    result: IdentificationResult
    manual_values: tuple[tuple[str, str], ...] = ()
    history: tuple[IdentificationResult, ...] = ()


class IdentityQueries(Protocol):
    def read(self, identity: UUID) -> IdentityView | None: ...


class IdentityRepository(Protocol):
    def save(self, command: IdentityEdit) -> IdentityView: ...
