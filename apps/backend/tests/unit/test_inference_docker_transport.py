from pathlib import Path
from unittest.mock import patch

import pytest

from garimpei.config.env import load_config
from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.gateway.inference.docker_transport import DockerOllamaTransport


@pytest.mark.parametrize("body", [b"", b"{}", b'{"done":'])
@patch("garimpei.infra.gateway.inference.docker_transport._Session")
def test_truncated_http_after_dispatch_requires_execution_proof(
    _session: object, tmp_path: Path, body: bytes
) -> None:
    transport = DockerOllamaTransport(load_config({}, root=tmp_path, require_secrets=False))
    raw = b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\n" + body
    with patch(
        "garimpei.infra.gateway.inference.docker_transport.owned_model_container",
        return_value="owned",
    ):
        with patch("garimpei.infra.gateway.inference.docker_transport._exchange", return_value=raw):
            with pytest.raises(InferenceError, match="execution_unknown"):
                transport.request("/api/chat", {"model": "test"}, 3)


@patch("garimpei.infra.gateway.inference.docker_transport._Session")
def test_complete_http_invalid_json_is_explicitly_rejected(
    _session: object, tmp_path: Path
) -> None:
    transport = DockerOllamaTransport(load_config({}, root=tmp_path, require_secrets=False))
    raw = b"HTTP/1.1 200 OK\r\nContent-Length: 1\r\n\r\nx"
    with patch(
        "garimpei.infra.gateway.inference.docker_transport.owned_model_container",
        return_value="owned",
    ):
        with patch("garimpei.infra.gateway.inference.docker_transport._exchange", return_value=raw):
            with pytest.raises(InferenceError, match="invalid_output"):
                transport.request("/api/chat", {"model": "test"}, 3)


def test_bad_framing_aborts_session_before_a_second_call_can_read_stale_bytes() -> None:
    import io
    import subprocess
    from threading import Event, Lock
    from typing import cast

    from garimpei.infra.gateway.inference.docker_transport import _Session

    class ScriptedPipe:
        def __init__(self) -> None:
            self.chunks = [
                b"HTTP/1.1 200 OK\r\nContent-Length: invalid\r\n\r\n",
                b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n{}",
            ]

        def read1(self, size: int) -> bytes:
            return self.chunks.pop(0) if self.chunks else b""

    class FakeBridgeProcess:
        def __init__(self) -> None:
            self.stdin = io.BytesIO()
            self.stdout = ScriptedPipe()
            self.killed = False

        def kill(self) -> None:
            self.killed = True

        def poll(self) -> int | None:
            return -9 if self.killed else None

    process = FakeBridgeProcess()
    session = _Session.__new__(_Session)
    session._process = cast(subprocess.Popen[bytes], process)
    session._ready, session._lock = Event(), Lock()
    session._ready.set()
    with pytest.raises(InferenceError, match="execution_unknown"):
        session.request(b"first", 1, True)
    assert process.killed
    with pytest.raises(InferenceError, match="service_unavailable"):
        session.request(b"second", 1, True)
    assert len(process.stdout.chunks) == 1
