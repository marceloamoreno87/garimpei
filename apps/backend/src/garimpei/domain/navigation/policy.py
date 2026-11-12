from dataclasses import dataclass
from datetime import datetime, timedelta

from garimpei.domain.navigation.work import Turn


@dataclass(frozen=True)
class NavigationPolicy:
    slice_seconds: int = 120
    slice_pages: int = 2
    slice_details: int = 10
    cycle_pages: int = 100
    cycle_terms: int = 3
    pending_details: int = 500
    suggestion_seconds: int = 45
    suggestion_pages: int = 1
    suggestion_details: int = 1
    suggestion_interval: int = 300
    suggestion_limit: int = 100
    evidence_limit: int = 10
    margin: int = 5

    def __post_init__(self) -> None:
        values = (
            self.slice_seconds,
            self.slice_pages,
            self.slice_details,
            self.cycle_pages,
            self.cycle_terms,
            self.pending_details,
            self.suggestion_seconds,
            self.suggestion_pages,
            self.suggestion_details,
            self.suggestion_interval,
            self.suggestion_limit,
            self.evidence_limit,
            self.margin,
        )
        if any(value <= 0 for value in values) or self.cycle_terms > 3:
            raise ValueError("Navigation limits must be positive; at most three terms per cycle")
        if (
            self.slice_pages > self.cycle_pages
            or self.suggestion_seconds >= self.suggestion_interval
        ):
            raise ValueError("Navigation slice limits must fit their persistent window")


def select_turn(turns: tuple[Turn, ...], now: datetime) -> Turn | None:
    eligible = tuple(
        turn for turn in turns if turn.next_attempt_at is None or turn.next_attempt_at <= now
    )
    return min(
        eligible,
        key=lambda turn: (turn.last_turn, turn.interest, turn.front, str(turn.id)),
        default=None,
    )


@dataclass(frozen=True)
class SuggestionAdmission:
    allowed: bool
    reason: str
    next_at: datetime | None = None


def decide_suggestion(
    policy: NavigationPolicy,
    now: datetime,
    *,
    active_ready: bool,
    active_due: datetime | None,
    last_slice: datetime | None,
    timeout: int,
    cadence: float,
    source_until: datetime | None = None,
    suspended: bool = False,
    configured: bool = True,
    initialized: bool = True,
) -> SuggestionAdmission:
    if not configured:
        return SuggestionAdmission(False, "not_configured")
    if not initialized:
        return SuggestionAdmission(False, "initial_collection")
    if suspended:
        return SuggestionAdmission(False, "access_suspended")
    if source_until is not None and source_until > now:
        return SuggestionAdmission(False, "source_wait", source_until)
    if active_ready:
        return SuggestionAdmission(False, "active_work")
    if (
        active_due is not None
        and (active_due - now).total_seconds() < timeout + cadence + policy.margin
    ):
        return SuggestionAdmission(False, "active_due_soon", active_due)
    quota_due = last_slice + timedelta(seconds=policy.suggestion_interval) if last_slice else None
    if quota_due is not None and quota_due > now:
        return SuggestionAdmission(False, "cooldown", quota_due)
    if policy.suggestion_seconds < timeout + cadence:
        return SuggestionAdmission(False, "budget_too_short")
    return SuggestionAdmission(True, "idle_available")


def suggestion_capacity(
    policy: NavigationPolicy, *, new_suggestion: bool, suggestion_count: int, evidence_count: int
) -> str:
    if new_suggestion and suggestion_count >= policy.suggestion_limit:
        return "suggestion_limit"
    if evidence_count >= policy.evidence_limit:
        return "evidence_limit"
    return ""


def eligible_suggestion(
    policy: NavigationPolicy,
    now: datetime,
    *,
    active_ready: bool,
    active_due: datetime | None,
    last_slice: datetime | None,
    timeout: int,
    cadence: float,
) -> bool:
    return decide_suggestion(
        policy,
        now,
        active_ready=active_ready,
        active_due=active_due,
        last_slice=last_slice,
        timeout=timeout,
        cadence=cadence,
    ).allowed
