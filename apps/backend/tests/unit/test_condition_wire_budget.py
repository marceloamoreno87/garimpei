"""Schema formatting cannot consume a semantic inference budget; evidence remains byte exact."""

import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

from garimpei.config.env import load_config
from garimpei.domain.inference.condition_evidence import SCHEMA, VERSION
from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.gateway.inference.docker_transport import DockerOllamaTransport
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
            assert value.endswith(context), "The full evidence was shortened or rewritten"
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
