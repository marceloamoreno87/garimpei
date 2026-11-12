from pathlib import Path

import pytest

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer
from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
from tests.factories.inference import OllamaGatewayFake, inference_settings, serve_inference


def test_connection_loss_after_dispatch_never_means_safe_retry(tmp_path: Path) -> None:
    fake = OllamaGatewayFake(mode="disconnect")
    with serve_inference(fake) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        guard = HostGpuGuard(settings.gpu_lock, settings.owner)
        assert guard.reserve()
        gateway = OllamaGateway(settings, guard, lambda: False)
        with pytest.raises(InferenceError, match="execution_unknown"):
            gateway.infer(PreparedPart("text", "Íntegro"), LocalInputPreparer(settings).artifact())
    assert fake.calls.count("/api/chat") == 1


def test_two_environments_cannot_steal_gpu_ownership(tmp_path: Path) -> None:
    first, second = (
        HostGpuGuard(tmp_path / "gpu.json", "a"),
        HostGpuGuard(tmp_path / "gpu.json", "b"),
    )
    assert first.reserve()
    assert not second.reserve()
    second.release()
    assert first.owned()
    first.release()
    assert second.reserve()


def test_valid_response_stays_structured_without_business_effects(tmp_path: Path) -> None:
    fake = OllamaGatewayFake()
    with serve_inference(fake) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        guard = HostGpuGuard(settings.gpu_lock, settings.owner)
        assert guard.reserve()
        gateway = OllamaGateway(settings, guard, lambda: False)
        result = gateway.infer(
            PreparedPart("text", "Íntegro"), LocalInputPreparer(settings).artifact()
        )
        assert "findings" in str(result["content"])
        assert "size_vram" in str(result["metrics"])
        assert gateway.recover() is False


@pytest.mark.parametrize(
    "field,value", [("prompt_eval_count", "invalid"), ("eval_count", float("inf"))]
)
def test_invalid_response_metrics_are_rejected_without_escaping_domain(
    tmp_path: Path, field: str, value: object
) -> None:
    settings = inference_settings(tmp_path, "http://127.0.0.1:12345")
    gateway = OllamaGateway(
        settings, HostGpuGuard(settings.gpu_lock, settings.owner), lambda: False
    )
    envelope = OllamaGatewayFake().respond("/api/chat")
    envelope[field] = value
    with pytest.raises(InferenceError, match="invalid_output"):
        gateway._validated_envelope(envelope)


def test_total_deadline_stops_a_trickling_response(tmp_path: Path) -> None:
    import time

    fake = OllamaGatewayFake(mode="drip")
    with serve_inference(fake) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        gateway = OllamaGateway(
            settings, HostGpuGuard(settings.gpu_lock, settings.owner), lambda: False
        )
        started = time.monotonic()
        with pytest.raises(InferenceError, match="execution_unknown|timeout"):
            gateway._request("/api/chat", {"model": "test"}, timeout=1)
        assert time.monotonic() - started < 2


def test_diagnostic_does_not_announce_unprobed_service(tmp_path: Path) -> None:
    settings = inference_settings(tmp_path, "http://127.0.0.1:9")
    gateway = OllamaGateway(
        settings, HostGpuGuard(settings.gpu_lock, settings.owner), lambda: False
    )
    status = gateway.diagnose()
    assert status["reason"] == "gpu_unavailable"
    assert status["service"] is False and status["resident"] is False
