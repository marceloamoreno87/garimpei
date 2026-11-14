"""Bounded Ollama HTTP over the private Compose inference network."""

import http.client
import json
import socket
import time
from threading import Timer
from typing import cast
from urllib.parse import urlsplit

from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.gateway.inference.json_encoding import compact_json


class HttpOllamaTransport:
    def __init__(self, endpoint: str) -> None:
        target = urlsplit(endpoint)
        if (
            target.scheme != "http"
            or target.hostname != "ollama"
            or target.port != 11434
            or target.path
            or target.username
            or target.password
            or target.query
            or target.fragment
        ):
            raise ValueError("Ollama endpoint: expected http://ollama:11434")
        self._host, self._port = target.hostname, target.port

    def request(
        self, path: str, body: dict[str, object] | None, timeout: float
    ) -> dict[str, object]:
        if (
            path not in {"/api/version", "/api/tags", "/api/show", "/api/ps", "/api/chat"}
            or not 0 < timeout <= 180
        ):
            raise InferenceError("service_unavailable", 503)
        connection = http.client.HTTPConnection(self._host, self._port, timeout=min(3, timeout))
        deadline = time.monotonic() + timeout
        dispatched = False
        timer: Timer | None = None
        try:
            connection.connect()
            sock = connection.sock
            remaining = max(0.001, deadline - time.monotonic())
            timer = Timer(remaining, _close, (connection, sock))
            timer.start()
            if sock is not None:
                sock.settimeout(remaining)
            dispatched = True
            connection.request(
                "POST" if body is not None else "GET",
                path,
                body=compact_json(body).encode() if body is not None else None,
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            raw = response.read(65537)
            if len(raw) > 65536:
                raise InferenceError("invalid_output")
            value = json.loads(raw)
            if response.status != 200:
                from garimpei.infra.gateway.inference.ollama_gateway import _error_cause

                raise InferenceError(_error_cause(value), 503)
            if not isinstance(value, dict):
                raise InferenceError("invalid_output")
            return cast(dict[str, object], value)
        except (OSError, http.client.HTTPException):
            raise InferenceError(
                "execution_unknown"
                if dispatched and path == "/api/chat"
                else "service_unavailable",
                503,
                sent=dispatched and path == "/api/chat",
            ) from None
        except ValueError:
            raise InferenceError("invalid_output") from None
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()


def _close(connection: http.client.HTTPConnection, sock: socket.socket | None) -> None:
    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
    connection.close()
