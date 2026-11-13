"""Bounded control-plane warmup and run-bound execution evidence, with no Django setup."""

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from garimpei.domain.inference.errors import InferenceError


class QualityPreflightError(RuntimeError):
    """Control-plane failure before corpus work is admitted or sent."""


class ReadinessGateway(Protocol):
    def diagnose(self) -> dict[str, object]: ...
    def unload(self) -> bool: ...


def wait_runtime_ready(
    gateway: ReadinessGateway,
    expected_model: str,
    *,
    max_wait_seconds: float = 15,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, object]:
    if not 0 < max_wait_seconds <= 15:
        raise ValueError("Runtime warmup must be positive and at most15seconds")
    started = clock()
    deadline = started + max_wait_seconds
    for attempt in range(1, 76):
        diagnostic = gateway.diagnose()
        reason = diagnostic.get("reason")
        if reason == "ready":
            if (
                diagnostic.get("service") is not True
                or diagnostic.get("artifact") != expected_model
            ):
                raise QualityPreflightError("runtime_readiness_proof_mismatch")
            try:
                unloaded = gateway.unload()
            except InferenceError as error:
                raise QualityPreflightError("runtime_unload_failed:" + error.code) from None
            if not unloaded:
                raise QualityPreflightError("runtime_unload_unconfirmed")
            return dict(
                reason="ready",
                attempts=attempt,
                elapsed_seconds=clock() - started,
                model_digest=expected_model,
            )
        if reason != "service_unavailable":
            raise QualityPreflightError("runtime_readiness_rejected:" + str(reason))
        remaining = deadline - clock()
        if remaining <= 0 or attempt == 75:
            raise QualityPreflightError("runtime_readiness_timeout")
        # A fresh Docker bridge becomes READY asynchronously; retry the same gateway only.
        sleep(min(0.2, remaining))
    raise QualityPreflightError("runtime_readiness_timeout")


def _execution_marker(
    output: Path,
    plan: dict[str, Any],
    stage: str,
    model_executed: bool | str,
    case_calls_sent: int | None,
    **details: Any,
) -> None:
    state = dict(
        schema_version=1,
        execution_id=plan.get("execution_id"),
        stage=stage,
        model_executed=model_executed,
        case_calls_sent=case_calls_sent,
        **details,
    )
    path = output.with_suffix(".execution.json")
    temporary = output.with_suffix(".execution.writing.json")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def execution_evidence(output: Path, execution_id: str) -> dict[str, object]:
    unknown: dict[str, object] = dict(model_executed="unknown")
    try:
        state = json.loads(output.with_suffix(".execution.json").read_text())
    except (OSError, ValueError):
        return unknown
    if (
        not isinstance(state, dict)
        or state.get("schema_version") != 1
        or state.get("execution_id") != execution_id
    ):
        return unknown
    model_executed = state.get("model_executed")
    calls = state.get("case_calls_sent")
    # Evidence from a stale/foreign run or an inconsistent marker cannot prove zero calls.
    if (
        model_executed is False
        and state.get("stage") in {"preflight", "preflight_failed", "corpus_progress"}
        and calls == 0
    ):
        return dict(
            model_executed=False,
            execution_stage=state["stage"],
            preflight_reason=state.get("reason"),
        )
    if model_executed is True and isinstance(calls, int) and calls > 0:
        return dict(model_executed=True, execution_stage=state.get("stage"), case_calls_sent=calls)
    return unknown
