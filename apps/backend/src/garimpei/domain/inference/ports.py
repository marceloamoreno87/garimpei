from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from garimpei.domain.inference.request import AnalysisInput

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class PreparedPart:
    key: str
    text: str
    image_id: str | None = None
    image_hash: str | None = None
    coverage: tuple[dict[str, object], ...] = ()
    model_digest: str = ""
    profile: str = "local-evidence-v1"


@dataclass(frozen=True)
class AnalysisTicket:
    request_id: UUID
    state: str
    reused: bool


@dataclass(frozen=True)
class AnalysisWork:
    request_id: UUID
    generation: int
    part_id: int
    artifact: str
    part: PreparedPart


@dataclass(frozen=True)
class InferenceStatus:
    revision: int
    paused: bool
    active: bool
    queued: int
    resident: bool
    reason: str
    checked_at: datetime | None
    model: str
    artifact: str
    service: bool
    last_result_at: datetime | None


class InputPreparer(Protocol):
    def prepare(self, value: AnalysisInput) -> tuple[PreparedPart, ...]: ...
    def artifact(self) -> str: ...


class InferenceGateway(Protocol):
    def infer(self, part: PreparedPart, artifact: str) -> dict[str, object]: ...
    def diagnose(self) -> dict[str, object]: ...
    def unload(self) -> bool: ...
    def recover(self) -> bool: ...


class InferenceRepository(Protocol):
    def admit(
        self, value: AnalysisInput, artifact: str, parts: tuple[PreparedPart, ...]
    ) -> AnalysisTicket: ...
    def claim(self, now: datetime) -> AnalysisWork | None: ...
    def authorize(self, work: AnalysisWork) -> bool: ...

    def publish(
        self,
        work: AnalysisWork,
        payload: dict[str, object],
        metrics: dict[str, object],
        now: datetime,
    ) -> bool: ...
    def failed(
        self, work: AnalysisWork, code: str, now: datetime, *, sent: bool = False
    ) -> None: ...
    def control(self, paused: bool, revision: int) -> None: ...
    def reconcile(self, now: datetime) -> None: ...
    def record_diagnostic(self, value: dict[str, object], now: datetime) -> None: ...
    def unloaded(self, confirmed: bool, now: datetime) -> None: ...
    def recovered(self, confirmed: bool, now: datetime) -> None: ...


class InferenceQueries(Protocol):
    def analysis(self, identity: UUID) -> dict[str, object]: ...
    def status(self) -> InferenceStatus: ...
