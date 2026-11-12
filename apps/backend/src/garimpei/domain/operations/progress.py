"""Useful progress follows committed business boundaries, never technical heartbeats."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


class ProgressConflict(Exception):
    pass


@dataclass
class OperationalProgress:
    id: UUID
    stage: str
    key: str
    revision: int
    generation: int
    pending_since: datetime
    last_progress_at: datetime | None = None
    last_attempt_at: datetime | None = None
    checkpoint: str = ""
    confirmed_boundaries: tuple[str, ...] = ()
    failures: int = 0
    pending: int = 1
    next_attempt_at: datetime | None = None
    reason: str = "pending"
    suspended: bool = False

    @classmethod
    def create(cls, stage: str, key: str, *, revision: int, now: datetime) -> "OperationalProgress":
        if (
            stage
            not in {
                "listing",
                "valuation",
                "alert",
                "exploration",
                "maintenance",
                "inference",
                "media",
            }
            or revision < 0
        ):
            raise ValueError(
                "Operational stage/revision: expected a supported stage and nonnegative revision"
            )
        return cls(uuid4(), stage, key, revision, 0, now)

    def attempt(self, now: datetime) -> None:
        self.last_attempt_at = now

    def confirm(self, boundary: str, *, generation: int, revision: int, now: datetime) -> None:
        if generation != self.generation or revision != self.revision:
            raise ProgressConflict(
                "Operational result belongs to an obsolete generation or revision"
            )
        if not boundary or boundary in self.confirmed_boundaries:
            return
        self.confirmed_boundaries = (*self.confirmed_boundaries, boundary)
        self.checkpoint, self.last_progress_at = boundary, now
        self.failures, self.reason = 0, "progress_confirmed"

    def state_at(self, now: datetime) -> str:
        if not self.pending:
            return "idle"
        if self.suspended:
            return "suspended"
        if self.next_attempt_at is not None and self.next_attempt_at > now:
            return "waiting"
        last = self.last_progress_at or self.pending_since
        return "stalled" if (now - last).total_seconds() >= 180 else "running"

    def wait_until(self, deadline: datetime, reason: str) -> None:
        self.next_attempt_at, self.reason = deadline, reason

    def fail(self, reason: str, now: datetime) -> None:
        self.last_attempt_at, self.reason = now, reason
        self.failures += 1
        self.suspended = self.failures >= 3 or reason == "access_denied"

    def admits(self, now: datetime) -> bool:
        return (
            self.pending > 0
            and not self.suspended
            and (self.next_attempt_at is None or self.next_attempt_at <= now)
        )

    def resume(self, *, expected_revision: int, now: datetime) -> None:
        if expected_revision != self.revision or self.reason == "access_denied":
            raise ProgressConflict("Operational revision changed or access remains suspended")
        self.generation += 1
        self.failures, self.suspended, self.next_attempt_at = 0, False, now
        self.reason = "explicit_resume"

    def complete(self) -> None:
        self.pending = 0
