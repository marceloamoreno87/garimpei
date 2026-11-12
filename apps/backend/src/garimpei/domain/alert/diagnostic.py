from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from garimpei.domain.alert.first_eligibility import POLICY


class AlertDiagnosticReadFailed(Exception):
    pass


@dataclass(frozen=True)
class AlertHistory:
    reference: UUID
    kind: str
    state: str
    confirmed_at: datetime | None


@dataclass(frozen=True)
class AlertDiagnostic:
    listing_id: UUID
    state: str
    reason: str
    label: str
    first_alert_state: str
    reasons: tuple[str, ...]
    current_reason: str = "pending_evaluation"
    current_label: str = "Aguardando avaliação do primeiro alerta"
    evaluated_at: datetime | None = None
    next_action_at: datetime | None = None
    observation_id: UUID | None = None
    configuration_revision: int | None = None
    valuation_revision: int | None = None
    condition_revision: int | None = None
    displayed_observation_id: UUID | None = None
    matches_displayed_observation: bool = True
    publication_status: str = "missing"
    published_at: datetime | None = None
    first_alert_deadline: datetime | None = None
    history: tuple[AlertHistory, ...] = ()
    confirmed_at: datetime | None = None
    intent_reference: UUID | None = None
    policy: str = POLICY


class AlertDiagnosticQueries(Protocol):
    def read(
        self, listing_id: UUID, displayed_observation_id: UUID | None
    ) -> AlertDiagnostic | None: ...
