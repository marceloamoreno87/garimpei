"""Schema formatting cannot consume a semantic inference budget; evidence remains byte exact."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from garimpei.config.env import load_config
from garimpei.domain.inference.condition_evidence import SCHEMA, VERSION
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import PreparedPart
from garimpei.infra.gateway.inference.docker_transport import DockerOllamaTransport
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
from tests.factories.inference import inference_settings
from tests.unit.test_inference_inputs import prepared


@pytest.mark.parametrize("compact_count,accepted", [(1378, True), (1537, False)])
def test_semantically_equal_schema_has_no_transport_whitespace_penalty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    compact_count: int,
    accepted: bool,
) -> None:
    preparer = prepared(tmp_path, monkeypatch)
    context = json.dumps(
        {
            "text": {
                "title": "iPhone 13 128GB",
                "description": "Funciona perfeitamente. Bateria trocada; saúde desconhecida. 日本語",
                "condition": "Usado",
            },
            "category": "electronics",
            "identity": "apple:iphone13:standard:128gb",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    original_schema = json.dumps(SCHEMA)
    compact_schema = json.dumps(SCHEMA, separators=(",", ":"), ensure_ascii=False)
    assert json.loads(original_schema) == json.loads(compact_schema)

    @dataclass
    class Encoding:
        ids: list[int]

    class CapturedEnvelopeCounter:
        @staticmethod
        def from_file(_path: str) -> "CapturedEnvelopeCounter":
            return CapturedEnvelopeCounter()

        def encode(self, value: str) -> Encoding:
            assert context in value, "The full evidence was shortened or rewritten"
            # Official-tokenizer reproduction: 1611 with pretty schema versus1378 compact.
            count = 1611 if original_schema in value else compact_count
            return Encoding([0] * (count - 256))

    monkeypatch.setattr(
        "garimpei.infra.gateway.inference.input_preparer.Tokenizer", CapturedEnvelopeCounter
    )
    if accepted:
        preparer._text_budget(context, VERSION, visual=True)
    else:
        with pytest.raises(InferenceError, match="context_unverified"):
            preparer._text_budget(context, VERSION, visual=True)
    assert preparer._settings.context_tokens == 4096


@patch("garimpei.infra.gateway.inference.docker_transport._Session")
def test_actual_wire_payload_is_compact_and_preserves_decoded_request(
    _session: object,
    tmp_path: Path,
) -> None:
    body: dict[str, object] = {
        "model": "pinned",
        "messages": [
            {"role": "user", "content": "Texto literal com espaços  duplos: 日本語 e condição."}
        ],
        "format": SCHEMA,
        "options": {"num_ctx": 4096, "num_predict": 1024},
        "truncate": False,
    }
    transport = DockerOllamaTransport(load_config({}, root=tmp_path, require_secrets=False))
    response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}"
    with patch(
        "garimpei.infra.gateway.inference.docker_transport.owned_model_container",
        return_value="owned",
    ):
        with patch(
            "garimpei.infra.gateway.inference.docker_transport._exchange", return_value=response
        ) as exchange:
            assert transport.request("/api/chat", body, 3) == {}
    sent = exchange.call_args.args[1]
    assert isinstance(sent, bytes)
    header, payload = sent.split(b"\r\n\r\n", 1)
    assert json.loads(payload) == body
    assert len(payload) < len(json.dumps(body).encode())
    assert f"Content-Length: {len(payload)}".encode() in header


@pytest.mark.parametrize(
    "invalid",
    [
        "invented_reference",
        "other_photo",
        "invented_literal",
        "missing_coverage",
        "conflicting_coverage",
    ],
)
def test_generation_schema_rejects_references_outside_the_physical_call(
    tmp_path: Path, invalid: str
) -> None:
    from copy import deepcopy

    from jsonschema import Draft202012Validator

    settings = inference_settings(tmp_path, "http://127.0.0.1:1")
    gateway = OllamaGateway(
        settings, HostGpuGuard(settings.gpu_lock, settings.owner), lambda: False
    )
    context = json.dumps({"text": {"description": "Funciona perfeitamente."}})
    part = PreparedPart(
        "photo", context, "current_photo", coverage=({"source_sha256": "a" * 64},), profile=VERSION
    )
    body = gateway._body(part)
    valid = {
        "schema_version": VERSION,
        "findings": [
            {
                "dimension": "function_claim",
                "assessment": "declaration",
                "description": "Declaração do vendedor",
                "references": ["t0"],
            }
        ],
        "conflicts": [],
        "limitations": [],
        "photo": {"status": "examined", "reason": "Visible image"},
    }
    validator = Draft202012Validator(cast(dict[str, object], body["format"]))
    assert validator.is_valid(valid)
    rejected = json.loads(json.dumps(deepcopy(valid)))
    if invalid == "invented_reference":
        rejected["findings"][0]["references"] = ["t999"]
    elif invalid == "other_photo":
        rejected["findings"][0]["references"] = ["i999"]
    elif invalid == "invented_literal":
        rejected["findings"][0]["references"] = [
            {"kind": "text", "field": "description", "quote": "Tudo original sem reparos."}
        ]
    elif invalid == "missing_coverage":
        rejected.pop("photo")
    else:
        rejected["photo"]["status"] = ["examined", "omitted"]
    assert not validator.is_valid(rejected)


def test_physical_reference_codes_expand_to_exact_evidence_before_consumption(
    tmp_path: Path,
) -> None:
    from garimpei.domain.inference.condition_evidence import validate_condition_result
    from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer
    from tests.factories.inference import OllamaGatewayFake, serve_inference

    class CompactEvidenceFake(OllamaGatewayFake):
        def respond(self, path: str) -> dict[str, object]:
            result = super().respond(path)
            if path == "/api/chat":
                result["message"] = dict(
                    role="assistant",
                    content=json.dumps(
                        {
                            "schema_version": VERSION,
                            "findings": [
                                {
                                    "dimension": "appearance",
                                    "assessment": "light_wear",
                                    "description": "Desgaste nas bordas",
                                    "references": ["i0", "t0"],
                                }
                            ],
                            "conflicts": [],
                            "limitations": [],
                            "photo": {"status": "examined", "reason": "Visible image"},
                        }
                    ),
                )
            return result

    context = json.dumps({"text": {"description": "Funciona perfeitamente. 日本語"}})
    with serve_inference(CompactEvidenceFake()) as endpoint:
        settings = inference_settings(tmp_path, endpoint)
        guard = HostGpuGuard(settings.gpu_lock, settings.owner)
        assert guard.reserve()
        gateway = OllamaGateway(settings, guard, lambda: False)
        result = gateway.infer(
            PreparedPart(
                "photo",
                context,
                "real_photo",
                coverage=({"source_sha256": "a" * 64},),
                profile=VERSION,
            ),
            LocalInputPreparer(settings).artifact(),
        )
    decoded = validate_condition_result(str(result["content"]), context, {"real_photo": "a" * 64})
    assert decoded["examined_photos"] == [{"photo_id": "real_photo", "sha256": "a" * 64}]
    findings = decoded["findings"]
    assert isinstance(findings, list)
    assert findings[0]["references"] == [
        {"kind": "image", "photo_id": "real_photo", "sha256": "a" * 64},
        {"kind": "text", "field": "description", "quote": "Funciona perfeitamente. 日本語"},
    ]


def test_token_counter_measures_the_exact_system_and_user_messages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from garimpei.domain.inference.condition_evidence import PROMPT

    preparer = prepared(tmp_path, monkeypatch)
    context = json.dumps({"text": {"description": "Funciona perfeitamente. 日本語"}})
    gateway = OllamaGateway(
        preparer._settings, HostGpuGuard(tmp_path / "guard", "test"), lambda: False
    )
    part = PreparedPart(
        "photo", context, "real_photo", coverage=({"source_sha256": "a" * 64},), profile=VERSION
    )
    body = gateway._body(part)
    messages = cast(list[dict[str, object]], body["messages"])
    expected = PROMPT + str(messages[1]["content"])

    class ActualMessageCounter:
        @staticmethod
        def from_file(_path: str) -> "ActualMessageCounter":
            return ActualMessageCounter()

        def encode(self, value: str) -> object:
            assert value == expected
            return type("Encoding", (), {"ids": [0] * 500})()

    monkeypatch.setattr(
        "garimpei.infra.gateway.inference.input_preparer.Tokenizer", ActualMessageCounter
    )
    preparer._text_budget(context, VERSION, visual=True, photo_id="real_photo", sha256="a" * 64)
