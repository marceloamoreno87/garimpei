from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from garimpei.domain.listing.assessment import Assessment

Clock = Callable[[], datetime]


@dataclass(frozen=True)
class AssessmentInput:
    listing_id: UUID
    observation_id: UUID
    observation_revision: int
    fingerprint: str
    model_revision: str
    snapshot: dict[str, object]


@dataclass(frozen=True)
class AssessmentWork:
    id: UUID
    generation: int
    value: AssessmentInput
    requests: tuple[UUID, ...] = ()
    pins: tuple[UUID, ...] = ()


class AssessmentInputs(Protocol):
    def read(self, identity: UUID) -> AssessmentInput: ...


class AssessmentRepository(Protocol):
    def prepare(self, value: AssessmentInput, now: datetime) -> AssessmentWork: ...
    def attach(
        self,
        work: AssessmentWork,
        requests: tuple[UUID, ...],
        pins: tuple[UUID, ...],
        now: datetime,
    ) -> None: ...
    def publish(self, work: AssessmentWork, value: Assessment, now: datetime) -> bool: ...
    def work(self, identity: UUID) -> AssessmentWork: ...


class AssessmentInference(Protocol):
    def submit(self, work: AssessmentWork) -> tuple[tuple[UUID, ...], tuple[UUID, ...]]: ...
    def result(self, work: AssessmentWork) -> Assessment | None: ...


class AssessmentError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
