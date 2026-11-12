from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

IdentityState = Literal[
    "identified",
    "unsupported_family",
    "missing_attribute",
    "conflicting_identity",
    "excluded_item",
    "unrecognized",
]
IDENTITY_POLICY = "evidence-identity-v1"


@dataclass(frozen=True)
class IdentityAttribute:
    name: str
    value: str
    origin: Literal["automatic", "manual"]
    observation_id: UUID
    input_revision: int
    field: str | None = None
    quote: str | None = None
    recorded_at: datetime | None = None
    reviewed_revision: int | None = None
    explicit: bool = True


@dataclass(frozen=True)
class AttributeConflict:
    name: str
    manual_value: str | None
    observed_value: str
    field: str | None = None
    quote: str | None = None

    @property
    def review_key(self) -> str:
        return f"{self.name}:{self.manual_value}:{self.observed_value}"


@dataclass(frozen=True)
class IdentificationResult:
    state: IdentityState
    observation_id: UUID
    input_revision: int
    family: str | None = None
    product_key: str | None = None
    attributes: tuple[IdentityAttribute, ...] = ()
    missing_attributes: tuple[str, ...] = ()
    conflicts: tuple[AttributeConflict, ...] = ()
    manual_revision: int = 0
    policy_version: str = IDENTITY_POLICY

    @property
    def reason(self) -> str | None:
        return {
            "identified": None,
            "unsupported_family": "familia_sem_suporte",
            "missing_attribute": "atributo_ausente",
            "conflicting_identity": "identidade_em_conflito",
            "excluded_item": "item_excluido",
            "unrecognized": "produto_indeterminado",
        }[self.state]
