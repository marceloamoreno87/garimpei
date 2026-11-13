"""Cold control-plane transport is retried without submitting corpus material."""

import json
from pathlib import Path

import pytest

from tests.factories import assessment_quality_execution as runtime

MODEL_DIGEST = "sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04"


class ControlledTime:
    value = 0.0

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class ColdGateway:
    def __init__(self, diagnostics: list[dict[str, object]], *, unload: bool = True) -> None:
        self._diagnostics = diagnostics
        self._unload = unload
        self.diagnoses = 0
        self.unloads = 0

    def diagnose(self) -> dict[str, object]:
        self.diagnoses += 1
        return self._diagnostics[min(self.diagnoses - 1, len(self._diagnostics) - 1)]

    def unload(self) -> bool:
        self.unloads += 1
        return self._unload


def ready() -> dict[str, object]:
    return dict(service=True, resident=False, reason="ready", artifact=MODEL_DIGEST)


def test_fresh_transport_can_become_ready_on_same_gateway_before_verified_unload() -> None:
    clock = ControlledTime()
    gateway = ColdGateway([dict(service=False, reason="service_unavailable"), ready()])
    result = runtime.wait_runtime_ready(
        gateway, MODEL_DIGEST, clock=clock.monotonic, sleep=clock.sleep
    )
    assert gateway.diagnoses == 2 and gateway.unloads == 1
    assert result["attempts"] == 2 and result["reason"] == "ready"
    assert 0 < clock.value <= 15


def test_permanent_transport_absence_times_out_without_unloading_or_inference() -> None:
    clock = ControlledTime()
    gateway = ColdGateway([dict(service=False, reason="service_unavailable")])
    with pytest.raises(runtime.QualityPreflightError, match="runtime_readiness_timeout"):
        runtime.wait_runtime_ready(
            gateway, MODEL_DIGEST, max_wait_seconds=1, clock=clock.monotonic, sleep=clock.sleep
        )
    assert 1 <= clock.value <= 1.2 and gateway.unloads == 0
    assert gateway.diagnoses <= 7


@pytest.mark.parametrize(
    "reason", ["artifact_mismatch", "gpu_unavailable", "model_missing", "invalid_output"]
)
def test_definitive_readiness_failure_is_not_retried(reason: str) -> None:
    clock = ControlledTime()
    gateway = ColdGateway([dict(service=True, reason=reason)])
    with pytest.raises(runtime.QualityPreflightError, match="runtime_readiness_rejected:" + reason):
        runtime.wait_runtime_ready(gateway, MODEL_DIGEST, clock=clock.monotonic, sleep=clock.sleep)
    assert gateway.diagnoses == 1 and gateway.unloads == 0 and clock.value == 0


@pytest.mark.parametrize("fault", ["digest", "service", "unload"])
def test_ready_word_does_not_bypass_artifact_service_or_unload_proof(fault: str) -> None:
    diagnostic = ready()
    if fault == "digest":
        diagnostic["artifact"] = "sha256:" + "0" * 64
    if fault == "service":
        diagnostic["service"] = False
    gateway = ColdGateway([diagnostic], unload=fault != "unload")
    with pytest.raises(runtime.QualityPreflightError):
        runtime.wait_runtime_ready(gateway, MODEL_DIGEST)
    assert gateway.unloads == (1 if fault == "unload" else 0)


def test_execution_evidence_is_bound_to_current_run_before_reporting_false(tmp_path: Path) -> None:
    output = tmp_path / "controlled-output.json"
    sidecar = output.with_suffix(".execution.json")
    sidecar.write_text(
        json.dumps(
            dict(
                schema_version=1,
                execution_id="old-run",
                model_executed=False,
                stage="preflight",
                case_calls_sent=0,
                reason="runtime_readiness_timeout",
            )
        )
    )
    assert runtime.execution_evidence(output, "new-run")["model_executed"] == "unknown"
    sidecar.write_text(
        json.dumps(
            dict(
                schema_version=1,
                execution_id="new-run",
                model_executed=False,
                stage="preflight",
                case_calls_sent=0,
                reason="runtime_readiness_timeout",
            )
        )
    )
    assert runtime.execution_evidence(output, "new-run")["model_executed"] is False


def test_execution_proof_can_be_read_by_cli_without_django_setup(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys

    environment = dict(os.environ)
    environment.pop("DJANGO_SETTINGS_MODULE", None)
    code = "from pathlib import Path;from tests.factories.assessment_quality_execution import execution_evidence;assert execution_evidence(Path('not-created.json'),'not-started')['model_executed']=='unknown'"
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=environment
    )
    assert result.returncode == 0, result.stderr


def test_failed_cold_preflight_records_zero_corpus_calls_before_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace
    from types import SimpleNamespace

    from tests.factories import assessment_quality_runtime as driver
    from tests.factories.inference import inference_settings

    settings = replace(inference_settings(tmp_path, "http://127.0.0.1:1"), service_enabled=True)
    monkeypatch.setattr(driver, "require_disposable", lambda: None)
    monkeypatch.setattr(driver, "load_inference_settings", lambda: settings)
    monkeypatch.setattr(driver, "load_alert_settings", lambda: SimpleNamespace(enabled=False))
    empty = SimpleNamespace(
        objects=SimpleNamespace(filter=lambda **kwargs: SimpleNamespace(exists=lambda: False))
    )
    monkeypatch.setattr(driver, "InferenceRequest", empty)
    monkeypatch.setattr(driver, "InferenceControl", empty)
    gateway = ColdGateway([dict(service=True, reason="artifact_mismatch")])
    monkeypatch.setattr(driver, "build_inference_gateway", lambda: gateway)

    def forbidden(*args: object) -> None:
        raise AssertionError("Preflight failure started a corpus case")

    monkeypatch.setattr(driver, "run_case", forbidden)
    plan = tmp_path / "preflight-plan.json"
    plan.write_text(
        json.dumps(
            dict(execution_id="controlled-current-run", reference_method="ai_assisted", cases=[])
        )
    )
    output = tmp_path / "not-executed.json"
    with pytest.raises(
        runtime.QualityPreflightError, match="runtime_readiness_rejected:artifact_mismatch"
    ):
        driver.execute(plan, output)
    evidence = runtime.execution_evidence(output, "controlled-current-run")
    assert evidence["model_executed"] is False
    assert evidence["preflight_reason"] == "runtime_readiness_rejected:artifact_mismatch"
    assert not output.exists() and gateway.unloads == 0


def test_cli_failure_preserves_known_false_from_its_own_child_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess
    from types import SimpleNamespace

    from tests.factories.assessment_quality import _execute

    output = tmp_path / "controlled-child.json"
    resumed: list[int] = []

    class ControlledInstance:
        def __init__(self, root: Path, env: Path) -> None:
            self.config = SimpleNamespace(environment="eval")
            self.manifest = dict(disposable=True)

        def command(self, *arguments: str, timeout: int) -> subprocess.CompletedProcess[str]:
            plan = json.loads(output.with_suffix(".inputs.json").read_text())
            output.with_suffix(".execution.json").write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        execution_id=plan["execution_id"],
                        stage="preflight_failed",
                        model_executed=False,
                        case_calls_sent=0,
                        reason="runtime_readiness_timeout",
                    )
                )
            )
            return subprocess.CompletedProcess(
                list(arguments), 1, "controlled preflight", "controlled timeout"
            )

    monkeypatch.setattr("tests.factories.runtime.FoundationInstance", ControlledInstance)
    monkeypatch.setattr("tests.factories.runtime.pause_worker", lambda instance: 123)
    monkeypatch.setattr(
        "tests.factories.runtime.resume_worker", lambda group: resumed.append(group)
    )
    result = _execute(
        dict(runtime_env="controlled-env", output=str(output)),
        dict(reference_method="ai_assisted", independent_human_review=False, cases=[]),
    )
    assert result["state"] == "blocked" and result["model_executed"] is False
    assert result["preflight_reason"] == "runtime_readiness_timeout" and resumed == [123]
