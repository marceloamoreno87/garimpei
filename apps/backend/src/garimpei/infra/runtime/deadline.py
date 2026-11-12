"""Remaining wall time for one startup and its owned rollback operations."""

import time

from garimpei.infra.runtime.manifest import OperationError


def remaining(deadline: float | None, *, maximum: float = 30, minimum: float = 0) -> float:
    seconds = maximum if deadline is None else min(maximum, deadline - time.monotonic())
    if seconds <= minimum:
        raise OperationError("Startup deadline exhausted; readiness was not confirmed")
    return seconds
