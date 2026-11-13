"""Validate attributed reference exports or run F15 quality only in an explicitly selected real eval runtime."""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tests.factories.assessment_quality_review import ReviewPending, read_plan


def evaluate_corpus(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"action", "manifest", "review", "package", "mode", "runtime_env", "output"}
    if set(payload) - allowed or payload.get("mode", "validate") not in {"validate", "real"}:
        return dict(
            state="blocked", reason="unexpected_corpus_action_fields_or_mode", model_executed=False
        )
    required = ("manifest", "review", "package")
    if any(not payload.get(key) for key in required):
        return dict(
            state="blocked", reason="manifest_review_package_required", model_executed=False
        )
    try:
        plan = read_plan(
            Path(payload["manifest"]), Path(payload["review"]), Path(payload["package"])
        )
    except (ReviewPending, OSError, ValueError, KeyError, TypeError) as error:
        return dict(
            state="blocked",
            reason="reference_or_frozen_input_incomplete",
            detail=str(error) if isinstance(error, ReviewPending) else type(error).__name__,
            model_executed=False,
        )
    if payload.get("mode") != "real":
        return dict(
            state="validated",
            model_executed=False,
            cases=len(plan["cases"]),
            reference_method=plan["reference_method"],
            independent_human_review=plan["independent_human_review"],
            review_sha256=plan["review_sha256"],
        )
    if not payload.get("runtime_env") or not payload.get("output"):
        return dict(
            state="blocked",
            reason="separate_real_eval_runtime_and_output_required",
            model_executed=False,
        )
    try:
        return _execute(payload, plan)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        return dict(
            state="blocked",
            reason="owned_runtime_precondition_or_execution_failed",
            detail=type(error).__name__,
            model_executed="unknown",
        )


def _execute(payload: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    from tests.factories.runtime import FoundationInstance, pause_worker, resume_worker

    root = Path(__file__).resolve().parents[4]
    instance = FoundationInstance(root, Path(payload["runtime_env"]).resolve())
    config = instance.config
    if config.environment != "eval" or not instance.manifest.get("disposable"):
        return dict(state="blocked", reason="owned_disposable_eval_required", model_executed=False)
    output = Path(payload["output"]).resolve()
    if output.is_relative_to(root) or output.exists():
        return dict(
            state="blocked", reason="new_output_outside_repository_required", model_executed=False
        )
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    plan_path = output.with_suffix(".inputs.json")
    with plan_path.open("x") as stream:
        json.dump(plan, stream, ensure_ascii=False)
    plan_path.chmod(0o600)
    group = pause_worker(instance)
    try:
        script = (
            "from pathlib import Path;from tests.factories.assessment_quality_runtime import execute;"
            + "execute(Path("
            + repr(str(plan_path))
            + "),Path("
            + repr(str(output))
            + "))"
        )
        budget = 120 + sum(
            max(600, len(case["photos"]) * 600)
            for case in plan["cases"]
            if case["split"] == "reserved"
        )
        result = instance.command(
            "uv",
            "run",
            "--project",
            "apps/backend",
            "--frozen",
            "--no-sync",
            "python",
            "apps/backend/manage.py",
            "shell",
            "-c",
            script,
            timeout=budget,
        )
    finally:
        resume_worker(group)
    if result.returncode:
        # Raw stderr may contain private runtime details; keep it outside reports/versioning.
        private = output.with_suffix(".private.txt")
        private.write_text(result.stdout + result.stderr)
        private.chmod(0o600)
        return dict(
            state="blocked",
            reason="real_runtime_failed_see_private_diagnostics",
            model_executed="unknown",
            output=str(output),
        )
    return dict(
        state="completed",
        model_executed=True,
        output=str(output),
        reference_method=plan["reference_method"],
        independent_human_review=plan["independent_human_review"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "review", "package", "runtime-env", "output"):
        parser.add_argument("--" + name, required=name in {"manifest", "review", "package"})
    parser.add_argument("--mode", choices=["validate", "real"], default="validate")
    result = evaluate_corpus(vars(parser.parse_args()))
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["state"] in {"validated", "completed"} else 2)


if __name__ == "__main__":
    main()
