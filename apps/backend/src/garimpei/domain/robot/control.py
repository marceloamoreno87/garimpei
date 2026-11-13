from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

RobotState = Literal["enabled", "draining", "disabled", "unknown", "unavailable"]
OperationOutcome = Literal["completed", "not_started", "unknown"]


@dataclass(frozen=True)
class RobotCommand:
    id: UUID
    enabled: bool
    revision: int


@dataclass(frozen=True)
class RobotStatus:
    enabled: bool
    revision: int
    changed_at: datetime
    state: RobotState
    active: int = 0
    unknown: int = 0
    worker_available: bool = False


@dataclass(frozen=True)
class RobotPermit:
    id: UUID
    stage: str
    unit_key: str
    input_revision: str
    resource_generation: int
    epoch: int


def effective_state(enabled: bool, active: int, unknown: int) -> RobotState:
    if unknown:
        return "unknown"
    if enabled:
        return "enabled"
    return "draining" if active else "disabled"
