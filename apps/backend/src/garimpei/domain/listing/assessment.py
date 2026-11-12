from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Reference:
    kind: str
    field: str = ""
    quote: str = ""
    photo_id: str = ""
    sha256: str = ""


@dataclass(frozen=True)
class Finding:
    dimension: str
    assessment: str
    description: str
    references: tuple[Reference, ...] = ()


@dataclass(frozen=True)
class Assessment:
    id: UUID | None = None
    observation_id: UUID | None = None
    fingerprint: str = ""
    policy_version: str = "condition-policy-v1"
    status: str = "waiting"
    reason: str = "waiting_inference"
    condition: str = "uncertain"
    sufficient: bool = False
    model_revision: str = ""
    analyzed_at: datetime | None = None
    findings: tuple[Finding, ...] = ()
    limitations: tuple[str, ...] = ()
    photo_coverage: tuple[dict[str, object], ...] = ()
    previous: UUID | None = None
    revision: int = 0


@dataclass(frozen=True)
class AssessmentDecision:
    condition: str
    sufficient: bool
    reason: str
