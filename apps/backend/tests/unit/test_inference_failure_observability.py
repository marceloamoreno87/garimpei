"""Rejected model output keeps bounded diagnostics, not private response text."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer
from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
from tests.factories.inference import OllamaGatewayFake, inference_settings, serve_inference


class LengthLimitedResponseFake(OllamaGatewayFake):
    def respond(self, path: str) -> dict[str, object]:
        response = super().respond(path)
        if path == "/api/chat":
            response.update(
                done_reason="length",
                total_duration=2_000_000_000,
                load_duration=500_000_000,
                prompt_eval_count=800,
                eval_count=512,
            )
            response["message"] = dict(
                role="assistant", content='PRIVATE RESPONSE MUST NOT ENTER METRICS {"findings":'
            )
        if path == "/api/ps":
            response["models"] = [
                dict(
                    name="qwen3.5:4b-q4_K_M",
                    size=3_000_000_000,
                    size_vram=3_000_000_000,
                    context_length=4096,
                )
            ]
        return response


@contextmanager
def controlled_gpu_samples() -> Iterator[list[dict[str, object]]]:
    yield [dict(scope="host", memory_mib=5000, utilization_percent=70)]


def test_rejected_length_envelope_keeps_reason_timing_and_gpu_without_private_content(
    tmp_path: Path,
) -> None:
    fake = LengthLimitedResponseFake()
    with serve_inference(fake) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        guard = HostGpuGuard(settings.gpu_lock, settings.owner)
        assert guard.reserve()
        gateway = OllamaGateway(settings, guard, lambda: False, monitor=controlled_gpu_samples)
        with pytest.raises(InferenceError, match="invalid_output") as captured:
            gateway.infer(
                PreparedPart("text", "Controlled input"), LocalInputPreparer(settings).artifact()
            )
        failure = captured.value
        assert failure.sent is True
        assert failure.diagnostic == "generation_length_limit"
        assert failure.metrics["total_duration"] == 2_000_000_000
        assert failure.metrics["load_duration"] == 500_000_000
        assert failure.metrics["eval_count"] == 512
        assert failure.metrics["size_vram"] == 3_000_000_000
        assert failure.metrics["context_length"] == 4096
        assert failure.metrics["gpu_samples"] == [
            dict(scope="host", memory_mib=5000, utilization_percent=70)
        ]
        assert "PRIVATE RESPONSE" not in str(failure.metrics)
        assert fake.calls.count("/api/chat") == 1


def test_stale_condition_profile_is_rejected_before_gpu_or_transport(tmp_path: Path) -> None:
    settings = inference_settings(tmp_path, "http://127.0.0.1:9")
    gateway = OllamaGateway(
        settings, HostGpuGuard(settings.gpu_lock, settings.owner), lambda: False
    )
    with pytest.raises(InferenceError, match="unsupported_prompt_or_schema") as captured:
        gateway.infer(
            PreparedPart("text", "old profile", profile="condition-evidence-v1"),
            LocalInputPreparer(settings).artifact(),
        )
    assert captured.value.diagnostic == "unsupported_profile" and captured.value.sent is False


class ResidencyResponseFake(LengthLimitedResponseFake):
    def __init__(self, before: str) -> None:
        super().__init__()
        self.before = before
        self.probes = 0

    def respond(self, path: str) -> dict[str, object]:
        result = super().respond(path)
        if path != "/api/ps":
            return result
        self.probes += 1
        if self.probes == 1 and self.before == "absent":
            return dict(models=[])
        digest = (
            "sha256:" + "0" * 64
            if self.probes == 1 and self.before == "unverified"
            else self.digest
        )
        result["models"] = [
            dict(
                name="qwen3.5:4b-q4_K_M",
                digest=digest,
                size=3_000_000_000,
                size_vram=3_000_000_000,
                context_length=4096,
            )
        ]
        return result


@pytest.mark.parametrize("before", ["absent", "matching_model", "unverified"])
def test_failed_public_call_proves_residency_before_without_guessing_warmth(
    tmp_path: Path, before: str
) -> None:
    fake = ResidencyResponseFake(before)
    with serve_inference(fake) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        guard = HostGpuGuard(settings.gpu_lock, settings.owner)
        assert guard.reserve()
        gateway = OllamaGateway(settings, guard, lambda: False)
        with pytest.raises(InferenceError) as captured:
            gateway.infer(
                PreparedPart("text", "controlled"), LocalInputPreparer(settings).artifact()
            )
        metrics = captured.value.metrics
        assert metrics["residency_before"] == before
        assert ("resident_before_digest" in metrics) is (before == "matching_model")
        duration = metrics["wall_duration_ns"]
        assert isinstance(duration, int) and duration > 0
        assert fake.calls.count("/api/chat") == 1


class MalformedOptionalMetricsFake(OllamaGatewayFake):
    def __init__(self, invalid: object) -> None:
        super().__init__()
        self.invalid = invalid

    def respond(self, path: str) -> dict[str, object]:
        result = super().respond(path)
        if path == "/api/chat":
            result.update(total_duration=self.invalid, load_duration={"raw": "CANARY"})
            result["message"] = dict(role="assistant", content="INVALID JSON")
        if path == "/api/ps":
            result["models"] = [
                dict(
                    name="qwen3.5:4b-q4_K_M",
                    size=10,
                    size_vram=10,
                    context_length="CANARY",
                )
            ]
        return result


@pytest.mark.parametrize("invalid", ["CANARY", None, True, -1, 2**63, float("inf")])
def test_successful_envelope_never_reintroduces_untrusted_optional_metrics(
    tmp_path: Path, invalid: object
) -> None:
    fake = MalformedOptionalMetricsFake(invalid)
    with serve_inference(fake) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        guard = HostGpuGuard(settings.gpu_lock, settings.owner)
        assert guard.reserve()
        gateway = OllamaGateway(settings, guard, lambda: False)
        result = gateway.infer(
            PreparedPart("text", "controlled"), LocalInputPreparer(settings).artifact()
        )
        metrics = result["metrics"]
        assert isinstance(metrics, dict)
        assert not {"total_duration", "load_duration", "context_length"} & metrics.keys()
        assert metrics["size_vram"] == 10 and metrics["eval_count"] == 40
        assert "CANARY" not in str(metrics)
