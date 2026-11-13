"""F23 typed targets preserve legacy caches and dispatch finite review profiles."""

import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import PreparedPart
from garimpei.domain.inference.request import AnalysisInput, ImageReference
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
from tests.factories.inference import inference_settings
from tests.unit.test_inference_inputs import prepared


@pytest.mark.parametrize(
    "profile,expected",
    [
        ("local-evidence-v1", "1aa65ce0c3b800c2553e0dbe1134ed21cc3f501f491af726a4e8ca9aca6f367f"),
        (
            "condition-evidence-v4",
            "5a32ecb4bd06e59235c3b479b252bed30081f4ddbec28803fe8af0040bbfcf2f",
        ),
    ],
)
def test_existing_profile_signatures_match_committed_f19_f15_evidence(
    profile: str,
    expected: str,
) -> None:
    # Hashes independently computed from committed 15079aa before the typed-target evolution.
    value = AnalysisInput(
        UUID(int=1),
        1,
        "Sony PS5 825GB",
        (),
        profile,
        profile,
        UUID(int=2) if profile == "condition-evidence-v4" else None,
        1 if profile == "condition-evidence-v4" else None,
    )
    assert value.signature("sha256:" + "a" * 64) == expected
    with pytest.raises(InferenceError, match="observation_required"):
        replace(value, observation_id=None)
    with pytest.raises(InferenceError, match="observation_required"):
        replace(value, target_kind="operations_snapshot")


def review_input(profile: str = "identity-review-v1") -> AnalysisInput:
    target = uuid4()
    return AnalysisInput(
        target,
        1,
        json.dumps(
            {"facts": [], "allowed_values": {"model": ["PS5"]}, "required_fields": ["model"]}
        ),
        (),
        profile,
        profile,
        target_id=target,
        target_revision=1,
        context={"manual_revision": 1, "policy": "assisted-evidence-v1"},
    )


def test_typed_context_and_profile_separate_cache_without_fabricated_observations() -> None:
    value = review_input()
    assert value.signature("model") != replace(
        value, context={"manual_revision": 2, "policy": "assisted-evidence-v1"}
    ).signature("model")
    with pytest.raises(InferenceError, match="invalid_profile_target"):
        replace(value, observation_id=None, target_kind="operations_snapshot")
    with pytest.raises(InferenceError, match="observation_revision_mismatch"):
        replace(value, target_id=uuid4())
    with pytest.raises(InferenceError, match="typed_target_required"):
        replace(value, target_revision=0)
    operations = replace(
        value,
        observation_id=None,
        target_kind="operations_snapshot",
        prompt_version="operations-support-v1",
        schema_version="operations-support-v1",
    )
    assert operations.signature("model")
    with pytest.raises(InferenceError, match="invalid_profile_target"):
        replace(operations, images=(ImageReference("private-photo", 1, "a" * 64),))
    with pytest.raises(InferenceError, match="non_listing_observation_forbidden"):
        replace(operations, observation_id=uuid4())


def test_new_profile_survives_input_preparation_and_reaches_finite_ollama_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preparer = prepared(tmp_path, monkeypatch)
    value = review_input()
    parts = preparer.prepare(value)
    assert parts[0].profile == value.prompt_version
    (tmp_path / "gateway").mkdir()
    settings = inference_settings(tmp_path / "gateway", "http://127.0.0.1:1")
    gateway = OllamaGateway(
        settings, HostGpuGuard(settings.gpu_lock, settings.owner), lambda: False
    )
    body = gateway._body(PreparedPart("text", value.text, profile=value.prompt_version))
    options = body["options"]
    assert isinstance(options, dict) and options["num_predict"] == 512
    assert options["num_ctx"] == 4096
    assert body["format"] != {"type": "object"}
    messages = body["messages"]
    assert isinstance(messages, list) and messages[1]["content"] == value.text
