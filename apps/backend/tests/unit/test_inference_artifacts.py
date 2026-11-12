import json
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import uuid4

import pytest
from django.core.management.base import CommandError

from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.input_preparer import read_lock
from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
from garimpei.infra.persistence.management.commands import local_ai
from tests.factories.inference import OllamaGatewayFake, inference_settings, serve_inference


def approved_lock() -> dict[str, object]:
    root = Path(__file__).resolve().parents[4]
    return cast(
        dict[str, object],
        json.loads(
            (root / "docs/F19-inferencia-multimodal-local-em-docker/model-lock.json").read_text()
        ),
    )


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("image", "ollama/ollama:latest", "artifact_mismatch"),
        ("image", "ollama/ollama:0.0.0@sha256:" + "f" * 64, "artifact_mismatch"),
        ("image", "ollama/ollama:0.40.16@sha256:short", "artifact_mismatch"),
        ("image", None, "artifact_incomplete"),
        ("manifest", {"schemaVersion": 2, "layers": []}, "artifact_incomplete"),
        ("model", "different-model:latest", "artifact_mismatch"),
        ("server_version", "0.0.0", "artifact_mismatch"),
        ("model_digest", "sha256:" + "f" * 64, "artifact_mismatch"),
        ("required_capabilities", ["completion"], "artifact_mismatch"),
        ("quantization", "Q8_0", "artifact_mismatch"),
        ("tokenizer", {"sha256": "a" * 64}, "artifact_incomplete"),
    ],
)
def test_invalid_pins_are_rejected_before_runtime(
    tmp_path: Path, field: str, value: object, reason: str
) -> None:
    lock = approved_lock()
    if value is None:
        lock.pop(field)
    else:
        lock[field] = value
    path = tmp_path / "private-model-lock.json"
    path.write_text(json.dumps(lock))
    with pytest.raises(InferenceError, match=reason):
        read_lock(path)


def test_complete_approved_pins_remain_usable(tmp_path: Path) -> None:
    lock = approved_lock()
    path = tmp_path / "private-model-lock.json"
    path.write_text(json.dumps(lock))
    assert read_lock(path) == lock


def test_well_formed_but_divergent_tokenizer_pin_never_reports_ready(tmp_path: Path) -> None:
    fake = OllamaGatewayFake()
    with serve_inference(fake) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        guard = HostGpuGuard(settings.gpu_lock, settings.owner)
        assert guard.reserve()
        try:
            gateway = OllamaGateway(settings, guard, lambda: False)
            assert gateway.diagnose()["reason"] == "ready"
            lock = json.loads(settings.model_lock.read_text())
            lock["tokenizer"]["sha256"] = "0" * 64
            settings.model_lock.write_text(json.dumps(lock))
            fake.calls.clear()
            assert gateway.diagnose()["reason"] == "artifact_mismatch"
            assert fake.calls == []
            with pytest.raises(InferenceError, match="artifact_mismatch"):
                read_lock(settings.model_lock)
        finally:
            guard.release()


@pytest.mark.parametrize("missing", [True, False])
def test_absent_lock_and_malformed_lock_have_distinct_causes(tmp_path: Path, missing: bool) -> None:
    path = tmp_path / "private-model-lock.json"
    if not missing:
        path.write_text("{invalid")
    with pytest.raises(
        InferenceError, match="artifact_missing" if missing else "artifact_mismatch"
    ):
        read_lock(path)


@pytest.mark.parametrize("area", ["blob_digest", "blob_size", "tokenizer_url", "tokenizer_hash"])
def test_internally_divergent_artifacts_are_rejected(tmp_path: Path, area: str) -> None:
    lock = approved_lock()
    if area.startswith("blob"):
        manifest = cast(dict[str, object], lock["manifest"])
        layer = cast(list[dict[str, object]], manifest["layers"])[0]
        layer["digest" if area == "blob_digest" else "size"] = (
            "sha256:" + "f" * 64 if area == "blob_digest" else 123
        )
    else:
        tokenizer = cast(dict[str, object], lock["tokenizer"])
        tokenizer["url" if area == "tokenizer_url" else "sha256"] = (
            "https://example.invalid/other/tokenizer.json" if area == "tokenizer_url" else "short"
        )
    path = tmp_path / "private-model-lock.json"
    path.write_text(json.dumps(lock))
    with pytest.raises(InferenceError, match="artifact_mismatch"):
        read_lock(path)


@pytest.mark.parametrize(
    "reason,expected",
    [
        ("artifact_missing", 2),
        ("artifact_incomplete", 2),
        ("model_missing", 2),
        ("context_unverified", 2),
        ("gpu_unavailable", 2),
        ("service_unavailable", 2),
        ("artifact_mismatch", 1),
        ("model_corrupt", 1),
        ("invalid_output", 1),
    ],
)
def test_real_cli_maps_prerequisites_separately_from_failures(
    monkeypatch: pytest.MonkeyPatch, reason: str, expected: int
) -> None:
    def diagnostic_failure(self: local_ai.Command, options: local_ai.Options) -> None:
        raise InferenceError(reason, 503)

    monkeypatch.setattr(local_ai.Command, "_dispatch", diagnostic_failure)
    with pytest.raises(CommandError) as error:
        local_ai.Command().handle(action="status", download=False, fixture=None)
    assert error.value.returncode == expected
    assert reason in str(error.value)


def test_prepare_requires_explicit_download_before_starting_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(local_ai, "load_config", lambda: SimpleNamespace())
    monkeypatch.setattr(
        local_ai, "load_inference_settings", lambda: SimpleNamespace(service_enabled=False)
    )
    monkeypatch.setattr(local_ai, "build_inference_gateway", object)

    def forbidden_start() -> None:
        pytest.fail("prepare without --download must not start a service")

    monkeypatch.setattr(local_ai, "start_configured_inference", forbidden_start)
    with pytest.raises(CommandError) as error:
        local_ai.Command().handle(action="prepare", download=False, fixture=None)
    assert error.value.returncode == 2


def test_smoke_cli_emits_counts_without_private_result_or_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    identity = uuid4()
    private = "PRIVATE-SMOKE-CANARY"
    result = {
        "request_id": str(identity),
        "observation_id": str(uuid4()),
        "state": "succeeded",
        "revision": 1,
        "coverage": [{"kind": "text", "examined": True, "text": private, "path": private}],
        "parts": [
            {
                "state": "succeeded",
                "result": {"findings": [{"quote": private}], "thinking": private},
                "metrics": {
                    "eval_count": 7,
                    "thinking": private,
                    "gpu_samples": [{"memory_mib": 123, "scope": "host", "thinking": private}],
                },
            }
        ],
        "thinking": private,
    }

    class RequestAnalysisFake:
        def execute(self, value: object) -> SimpleNamespace:
            return SimpleNamespace(reused=False, request_id=identity)

    class ReadAnalysisFake:
        def execute(self, request: object) -> dict[str, object]:
            return result

    monkeypatch.setattr(
        local_ai, "load_config", lambda: SimpleNamespace(environment="eval", environment_id="pins")
    )
    monkeypatch.setattr(local_ai, "load_inference_settings", lambda: SimpleNamespace())
    monkeypatch.setattr(local_ai, "build_inference_gateway", object)
    monkeypatch.setattr(local_ai, "_smoke_observation", lambda *args: (identity, private))
    monkeypatch.setattr(local_ai, "build_request_analysis", RequestAnalysisFake)
    monkeypatch.setattr(local_ai, "build_read_analysis", ReadAnalysisFake)
    output = StringIO()
    local_ai.Command(stdout=output).handle(action="smoke", download=False, fixture="text")
    emitted = json.loads(output.getvalue())
    assert private not in output.getvalue()
    assert emitted["request_id"] == str(identity)
    assert emitted["state"] == "succeeded"
    assert emitted["parts"][0]["result_counts"]["findings"] == 1
    assert emitted["parts"][0]["metrics"]["eval_count"] == 7
    assert emitted["parts"][0]["metrics"]["gpu_samples"][0]["memory_mib"] == 123
    assert emitted["coverage"][0]["examined"] is True
