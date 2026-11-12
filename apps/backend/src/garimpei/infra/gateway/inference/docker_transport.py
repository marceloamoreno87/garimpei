"""REST on the container's loopback without attaching an outbound-capable network."""

import http.client
import json
import socket
import subprocess
import time
from io import BufferedReader, BytesIO
from threading import Event, Lock, Thread, Timer
from typing import BinaryIO, cast

from garimpei.config.env import RuntimeConfig
from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.runtime.inference_runtime import owned_model_container
from garimpei.infra.runtime.manifest import OperationError, read_manifest


class DockerOllamaTransport:
    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._session: _Session | None = None

    def request(
        self, path: str, body: dict[str, object] | None, timeout: float
    ) -> dict[str, object]:
        if path not in {"/api/version", "/api/tags", "/api/show", "/api/ps", "/api/chat"}:
            raise InferenceError("service_unavailable", 503)
        deadline = time.monotonic() + timeout
        try:
            identifier = self._reference(timeout)
        except OperationError:
            raise InferenceError("service_unavailable", 503) from None
        if identifier is None:
            raise InferenceError("service_unavailable", 503)
        payload = json.dumps(body).encode() if body is not None else b""
        header = (
            ("GET" if body is None else "POST") + " " + path + " HTTP/1.1\r\n"
            "Host: 127.0.0.1\r\nConnection: close\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(payload)}\r\n\r\n"
        ).encode()
        command = ["docker", "exec", "-i", identifier, "bash", "-c", _BRIDGE_SCRIPT]
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise InferenceError("service_unavailable", 503)
        if self._session is None or not self._session.alive():
            self._session = _Session(command)
        raw = _exchange(
            command, header + payload, remaining, path == "/api/chat", session=self._session
        )
        response = http.client.HTTPResponse(cast(socket.socket, _ResponseSocket(raw)))
        try:
            response.begin()
            content = response.read()
            if len(content) > 65536:
                raise InferenceError("invalid_output")
            value = json.loads(content)
        except http.client.HTTPException:
            raise InferenceError(
                "execution_unknown" if path == "/api/chat" else "service_unavailable", 503
            ) from None
        except ValueError:
            raise InferenceError("invalid_output") from None
        if response.status != 200:
            from garimpei.infra.gateway.inference.ollama_gateway import _error_cause

            raise InferenceError(_error_cause(value), 503)
        if not isinstance(value, dict):
            raise InferenceError("invalid_output")
        return cast(dict[str, object], value)

    def _reference(self, timeout: float) -> str | None:
        manifest = read_manifest(self._config.directory)
        if (
            manifest is not None
            and manifest["checkout"] == str(self._config.root)
            and manifest["environment_id"] == self._config.environment_id
            and manifest["run_id"] == self._config.run_id
            and manifest.get("inference_container")
        ):
            # Lifecycle verified immutable Docker labels before recording this full container ID.
            return manifest["inference_container"]
        return owned_model_container(self._config, timeout=timeout)


class _ResponseSocket:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    def makefile(self, _mode: str) -> BinaryIO:
        return BytesIO(self._raw)


_BRIDGE_SCRIPT = (
    "printf 'READY\\n'; "
    "while IFS= read -r n; do "
    'case "$n" in ""|*[!0-9]*) exit 2;; esac; '
    "exec 3<>/dev/tcp/127.0.0.1/11434 || exit 3; "
    'head -c "$n" >&3; cat <&3; exec 3<&-; exec 3>&-; done'
)


class _Session:
    def __init__(self, command: list[str]) -> None:
        self._process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        self._ready, self._lock = Event(), Lock()
        Thread(target=self._await_ready, daemon=True).start()

    def alive(self) -> bool:
        return self._process.poll() is None

    def _await_ready(self) -> None:
        stream = self._process.stdout
        if stream is not None and stream.readline(20).strip() == b"READY":
            self._ready.set()

    def request(self, payload: bytes, timeout: float, uncertain: bool) -> bytes:
        if not self._ready.is_set() or self._process.poll() is not None:
            raise InferenceError("service_unavailable", 503)
        if not self._lock.acquire(blocking=False):
            raise InferenceError("service_unavailable", 503)
        timer = Timer(timeout, self._process.kill)
        timer.start()
        try:
            return self._transfer(payload, uncertain)
        finally:
            timer.cancel()
            self._lock.release()

    def _transfer(self, payload: bytes, uncertain: bool) -> bytes:
        process = self._process
        assert process.stdin is not None and process.stdout is not None
        try:
            process.stdin.write(str(len(payload)).encode() + b"\n" + payload)
            process.stdin.flush()
            raw = _read_framed(cast(BufferedReader, process.stdout))
            if not raw:
                raise InferenceError(
                    "execution_unknown" if uncertain else "service_unavailable", 503, sent=uncertain
                )
            return raw
        except InferenceError:
            process.kill()
            raise InferenceError(
                "execution_unknown" if uncertain else "service_unavailable", 503, sent=uncertain
            ) from None
        except (OSError, ValueError):
            process.kill()
            raise InferenceError(
                "execution_unknown" if uncertain else "service_unavailable", 503, sent=uncertain
            ) from None


def _exchange(
    command: list[str],
    payload: bytes,
    timeout: float,
    uncertain: bool,
    *,
    session: _Session | None = None,
) -> bytes:
    client = session or _Session(command)
    return client.request(payload, timeout, uncertain)


def _read_framed(stream: BufferedReader) -> bytes:
    raw = b""
    while len(raw) <= 73728:
        chunk = stream.read1(4096)
        if not chunk:
            return raw
        raw += chunk
        if _framed_complete(raw):
            return raw
    raise InferenceError("execution_unknown", 503)


def _framed_complete(raw: bytes) -> bool:
    header, marker, body = raw.partition(b"\r\n\r\n")
    if not marker:
        return False
    lines = header.lower().split(b"\r\n")
    lengths = [
        line.partition(b":")[2].strip() for line in lines if line.startswith(b"content-length:")
    ]
    if lengths:
        if len(lengths) != 1 or not lengths[0].isdigit():
            raise InferenceError("invalid_output")
        return len(body) >= int(lengths[0])
    if b"transfer-encoding: chunked" in lines:
        response = http.client.HTTPResponse(cast(socket.socket, _ResponseSocket(raw)))
        try:
            response.begin()
            response.read()
            return True
        except http.client.HTTPException:
            return False
    return False
