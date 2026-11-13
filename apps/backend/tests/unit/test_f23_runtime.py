"""Transport boundaries and runtime configuration protect the container migration."""

import http.client
from pathlib import Path
from unittest.mock import Mock

import pytest

from garimpei.config.env import load_config
from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.gateway.inference.http_transport import HttpOllamaTransport


def test_container_database_uses_private_dns(tmp_path: Path) -> None:
    config = load_config(
        {
            "GARIMPEI_ENV": "eval",
            "GARIMPEI_INSTANCE": "f23_dns",
            "GARIMPEI_CONTAINERIZED": "true",
            "GARIMPEI_RUNTIME_ROOT": str(tmp_path / "state"),
            "POSTGRES_PASSWORD": "private-password",
        },
        root=tmp_path,
        require_secrets=False,
    )
    assert "@postgres:5432/garimpei_eval_f23_dns" in config.database_url
    assert config.directory == tmp_path / "state/eval_f23_dns"


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://ollama:11434",
        "http://remote.invalid:11434",
        "http://ollama:11434/path",
        "http://user:password@ollama:11434",
        "http://ollama:11434?cloud=true",
    ],
)
def test_transport_cannot_target_remote_or_credentialed_endpoint(endpoint: str) -> None:
    with pytest.raises(ValueError):
        HttpOllamaTransport(endpoint)


def test_uncertain_http_chat_cannot_be_reclassified_as_safe_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = Mock(spec=http.client.HTTPConnection)
    connection.sock = None
    connection.getresponse.side_effect = TimeoutError()
    monkeypatch.setattr(http.client, "HTTPConnection", lambda *_args, **_kwargs: connection)
    with pytest.raises(InferenceError) as failure:
        HttpOllamaTransport("http://ollama:11434").request("/api/chat", {"model": "local"}, 1)
    assert failure.value.code == "execution_unknown"
    assert failure.value.sent
    connection.close.assert_called()


def test_transport_reads_only_bounded_response(monkeypatch: pytest.MonkeyPatch) -> None:
    connection = Mock(spec=http.client.HTTPConnection)
    connection.sock = None
    response = Mock()
    response.status = 200
    response.read.return_value = b"x" * 65537
    connection.getresponse.return_value = response
    monkeypatch.setattr(http.client, "HTTPConnection", lambda *_args, **_kwargs: connection)
    with pytest.raises(InferenceError) as failure:
        HttpOllamaTransport("http://ollama:11434").request("/api/chat", {}, 1)
    assert failure.value.code == "invalid_output"
    response.read.assert_called_once_with(65537)
