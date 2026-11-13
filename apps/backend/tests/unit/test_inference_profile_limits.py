"""Approved F15 output budget never changes the F19 legacy or total context caps."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from garimpei.domain.inference.condition_evidence import VERSION
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import PreparedPart
from garimpei.domain.inference.request import AnalysisInput
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer
from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
from tests.factories.inference import OllamaGatewayFake, inference_settings, serve_inference


class ProfileLimitEnvelopeFake(OllamaGatewayFake):
    def __init__(self, generated: int, prompt: int) -> None:
        super().__init__()
        self.generated, self.prompt = generated, prompt

    def respond(self, path: str) -> dict[str, object]:
        result = super().respond(path)
        if path == "/api/chat":
            result.update(eval_count=self.generated, prompt_eval_count=self.prompt)
            result["message"] = dict(
                role="assistant",
                content=json.dumps(
                    dict(
                        schema_version=VERSION,
                        findings=[],
                        conflicts=[],
                        limitations=[],
                        photo=dict(status="not_provided", reason="No image"),
                    )
                ),
            )
        return result


@pytest.mark.parametrize(
    "profile,generated,prompt,accepted,reason",
    [
        ("local-evidence-v1", 511, 3584, True, ""),
        ("local-evidence-v1", 512, 100, False, "invalid_output"),
        ("local-evidence-v1", 1, 3585, False, "context_unverified"),
        (VERSION, 700, 3072, True, ""),
        (VERSION, 1024, 100, False, "invalid_output"),
        (VERSION, 700, 3073, False, "context_unverified"),
    ],
)
def test_dispatch_and_response_reserve_the_approved_profile_limit(
    tmp_path: Path, profile: str, generated: int, prompt: int, accepted: bool, reason: str
) -> None:
    fake = ProfileLimitEnvelopeFake(generated, prompt)
    with serve_inference(fake) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        guard = HostGpuGuard(settings.gpu_lock, settings.owner)
        assert guard.reserve()
        gateway = OllamaGateway(settings, guard, lambda: False)
        part = PreparedPart(
            "text",
            '{"text":{"title":"Controlled"}}' if profile == VERSION else "Controlled",
            profile=profile,
        )
        options = gateway._body(part)["options"]
        assert isinstance(options, dict)
        assert options["num_ctx"] == 4096
        assert options["num_predict"] == (1024 if profile == VERSION else 512)
        artifact = LocalInputPreparer(settings).artifact()
        if accepted:
            assert gateway.infer(part, artifact)["metrics"]
        else:
            with pytest.raises(InferenceError, match=reason):
                gateway.infer(part, artifact)


def test_condition_profile_revision_invalidates_both_prior_profiles() -> None:
    assert VERSION == "condition-evidence-v4"
    for version in ("condition-evidence-v1", "condition-evidence-v2", "condition-evidence-v3"):
        with pytest.raises(InferenceError, match="unsupported_prompt_or_schema"):
            AnalysisInput(uuid4(), 1, "Controlled", (), version, version, uuid4(), 1)


@pytest.mark.parametrize("field,value", [("context_tokens", 8192), ("output_tokens", 1024)])
def test_legacy_global_settings_cannot_expand_profile_or_context_limits(
    tmp_path: Path, field: str, value: int
) -> None:
    from dataclasses import replace

    from garimpei.config.env import ConfigurationError

    settings = inference_settings(tmp_path, "http://127.0.0.1:1")
    with pytest.raises(ConfigurationError, match="Inference budgets"):
        replace(settings, context_tokens=value) if field == "context_tokens" else replace(
            settings, output_tokens=value
        )


@pytest.mark.parametrize("count,accepted", [(1536, True), (1537, False)])
def test_condition_visual_preparation_preserves_visual_and_output_reservations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, count: int, accepted: bool
) -> None:
    from dataclasses import dataclass

    from tests.unit.test_inference_inputs import prepared

    @dataclass
    class Encoding:
        ids: list[int]

    class ControlledTokenCounter:
        @staticmethod
        def from_file(path: str) -> "ControlledTokenCounter":
            return ControlledTokenCounter()

        def encode(self, text: str) -> Encoding:
            return Encoding([0] * (count - 256))

    preparer = prepared(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "garimpei.infra.gateway.inference.input_preparer.Tokenizer", ControlledTokenCounter
    )
    # The same textual budget remains below legacy 2048; F15 must also reserve 1536 visual +1024 output.
    preparer._text_budget("Controlled", "local-evidence-v1")
    if accepted:
        preparer._text_budget('{"text":{"title":"Controlled"}}', VERSION, visual=True)
    else:
        with pytest.raises(InferenceError, match="context_unverified"):
            preparer._text_budget('{"text":{"title":"Controlled"}}', VERSION, visual=True)
