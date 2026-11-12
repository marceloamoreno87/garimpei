from dataclasses import dataclass

from garimpei.domain.listing.ports import CollectionPolicy, SourceFailure

STRUCTURAL_FAILURES = frozenset(
    {
        "category_unavailable",
        "window_limit",
        "repeated_page",
        "repeated_continuation",
        "wrong_category_context",
        "search_query_template_unavailable",
    }
)


@dataclass(frozen=True)
class RetrySchedule:
    failures: int
    delay: int
    suspended: bool


def retry_schedule(
    policy: CollectionPolicy,
    previous_failures: int,
    *,
    progress: bool,
    failures: tuple[SourceFailure, ...],
) -> RetrySchedule:
    structural = bool(failures) and all(f.reason in STRUCTURAL_FAILURES for f in failures)
    consecutive = 0 if progress or structural else previous_failures + 1
    delay = (
        policy.interval
        if consecutive == 0
        else min(policy.retry_max, policy.retry_base * 2 ** min(consecutive - 1, 16))
    )
    delay = max(delay, max((f.retry_after for f in failures), default=0))
    return RetrySchedule(consecutive, delay, any(f.access for f in failures))
