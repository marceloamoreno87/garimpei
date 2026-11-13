import base64
import hashlib
import http.client
import json
import socket
import time
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager, nullcontext
from threading import Timer, local
from typing import cast
from urllib.parse import urlsplit

from garimpei.config.env import InferenceSettings
from garimpei.domain.inference.condition_evidence import (
    PROMPT as CONDITION_PROMPT,
)
from garimpei.domain.inference.condition_evidence import (
    SCHEMA as CONDITION_SCHEMA,
)
from garimpei.domain.inference.condition_evidence import (
    VERSION as CONDITION_VERSION,
)
from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.ports import PreparedPart
from garimpei.domain.inference.request import MODEL, SUPPORTED_PROFILES
from garimpei.domain.inference.result import bounded_schema
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.gateway.inference.input_preparer import PROMPT, artifact_signature, read_lock


class OllamaGateway:
    def __init__(
        self,
        settings: InferenceSettings,
        guard: HostGpuGuard,
        recover_owned: Callable[[], bool],
        transport: Callable[[str, dict[str, object] | None, float], dict[str, object]]
        | None = None,
        monitor: Callable[[], AbstractContextManager[list[dict[str, object]]]] | None = None,
    ) -> None:
        self._settings, self._guard, self._recover_owned = settings, guard, recover_owned
        self._transport = transport
        self._monitor = monitor
        self._budget_state = _CallBudget()

    def infer(self, part: PreparedPart, artifact: str) -> dict[str, object]:
        with self._budget(self._settings.timeout):
            return self._run_part(part, artifact)

    def _run_part(self, part: PreparedPart, artifact: str) -> dict[str, object]:
        if part.profile not in SUPPORTED_PROFILES:
            raise InferenceError("unsupported_prompt_or_schema", diagnostic="unsupported_profile")
        lock = read_lock(self._settings.model_lock)
        current = artifact_signature(lock)
        if current != artifact:
            raise InferenceError("artifact_mismatch", 503)
        self._verify(lock)
        with self._guard.call(), self._monitor() if self._monitor else nullcontext([]) as samples:
            started = time.monotonic_ns()
            before = self._resident()
            metrics = _residency_before(before, str(lock["model_digest"]))
            received = False
            try:
                envelope = self._request(
                    "/api/chat", self._body(part), timeout=self._settings.timeout
                )
                received = True
                metrics.update(_response_metrics(envelope))
                result = self._validate_received(envelope)
                metrics.update(cast(dict[str, object], result["metrics"]))
                result["metrics"] = metrics | {
                    "gpu_samples": samples,
                    "wall_duration_ns": time.monotonic_ns() - started,
                }
                return result
            except InferenceError as error:
                # Numeric metadata and host samples remain useful even when generated JSON is rejected.
                # Never retain message/content/tool arguments in public failure telemetry.
                metrics.update(self._failure_residency() if received else {})
                raise InferenceError(
                    error.code,
                    error.status,
                    sent=received or error.sent,
                    diagnostic=error.diagnostic,
                    metrics=metrics
                    | error.metrics
                    | {"gpu_samples": samples, "wall_duration_ns": time.monotonic_ns() - started},
                ) from None

    def _validate_received(self, envelope: dict[str, object]) -> dict[str, object]:
        try:
            return self._validated_envelope(envelope)
        except InferenceError as error:
            raise InferenceError(
                error.code,
                error.status,
                sent=True,
                diagnostic=error.diagnostic,
                metrics=error.metrics,
            ) from None

    def _body(self, part: PreparedPart) -> dict[str, object]:
        content = part.text if part.image_id is None else "Examine image_id=" + part.image_id
        if part.profile == CONDITION_VERSION:
            content = part.text + (
                "\nFoto atual: "
                + json.dumps(
                    {
                        "photo_id": part.image_id,
                        "sha256": part.coverage[0].get(
                            "source_sha256", part.coverage[0].get("sha256")
                        ),
                    }
                )
                if part.image_id
                else ""
            )
        message: dict[str, object] = {"role": "user", "content": content}
        if part.image_hash:
            raw = (self._settings.directory / part.image_hash).read_bytes()
            if hashlib.sha256(raw).hexdigest() != part.image_hash:
                raise InferenceError("invalid_image_content")
            message["images"] = [base64.b64encode(raw).decode("ascii")]
        return {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": CONDITION_PROMPT if part.profile == CONDITION_VERSION else PROMPT,
                },
                message,
            ],
            "format": CONDITION_SCHEMA
            if part.profile == CONDITION_VERSION
            else bounded_schema(part.text, part.image_id),
            "stream": False,
            "think": False,
            "truncate": False,
            "shift": False,
            "keep_alive": "5m",
            "options": {
                "num_ctx": self._settings.context_tokens,
                "num_predict": self._settings.output_tokens,
                "temperature": 0,
            },
        }

    def _validated_envelope(self, envelope: dict[str, object]) -> dict[str, object]:
        message = envelope.get("message")
        if envelope.get("done") is not True:
            raise InferenceError("invalid_output", diagnostic="generation_incomplete")
        if envelope.get("done_reason") != "stop":
            raise InferenceError(
                "invalid_output",
                diagnostic="generation_length_limit"
                if envelope.get("done_reason") == "length"
                else "generation_stop_reason",
            )
        if (
            not isinstance(message, dict)
            or message.get("tool_calls")
            or message.get("role") != "assistant"
        ):
            raise InferenceError("invalid_output", diagnostic="assistant_message_or_tool_calls")
        if (
            _metric(envelope, "prompt_eval_count") + self._settings.output_tokens
            > self._settings.context_tokens
        ):
            raise InferenceError("context_unverified", diagnostic="response_context_budget")
        if _metric(envelope, "eval_count") >= self._settings.output_tokens:
            raise InferenceError("invalid_output", diagnostic="generation_token_limit")
        resident = self._resident()
        if resident is None or _metric(resident, "size_vram") < _metric(resident, "size"):
            raise InferenceError("gpu_degraded", 503)
        return {
            "content": message.get("content"),
            "metrics": _response_metrics(envelope) | _resident_metrics(resident),
        }

    def _failure_residency(self) -> dict[str, object]:
        try:
            resident = self._resident()
        except InferenceError as error:
            return {"residency_after_error": error.code}
        if resident is None:
            return {"residency_after": "absent"}
        return _resident_metrics(resident)

    def diagnose(self) -> dict[str, object]:
        self._budget_state.service_confirmed = False
        try:
            with self._budget(3):
                return self._diagnostic()
        except InferenceError as error:
            return {
                "service": self._budget_state.service_confirmed,
                "resident": False,
                "reason": error.code,
                "artifact": "",
            }

    def _diagnostic(self) -> dict[str, object]:
        lock = read_lock(self._settings.model_lock)
        self._verify(lock)
        resident = self._resident()
        return {
            "service": True,
            "resident": resident is not None,
            "reason": "ready",
            "artifact": lock["model_digest"],
        }

    @contextmanager
    def _budget(self, duration: float) -> Iterator[None]:
        previous = self._budget_state.deadline
        self._budget_state.deadline = time.monotonic() + duration
        try:
            yield
        finally:
            self._budget_state.deadline = previous

    def _verify(self, lock: dict[str, object]) -> None:
        if not self._guard.owned():
            raise InferenceError("gpu_unavailable", 503)
        version = self._request("/api/version").get("version")
        self._budget_state.service_confirmed = isinstance(version, str)
        if version != lock.get("server_version"):
            raise InferenceError("artifact_mismatch", 503)
        tags = cast(list[dict[str, object]], self._request("/api/tags").get("models", []))
        selected = next((row for row in tags if row.get("name") == MODEL), None)
        if selected is None:
            raise InferenceError("model_missing", 503)
        if str(selected.get("digest", "")).removeprefix("sha256:") != str(
            lock.get("model_digest", "")
        ).removeprefix("sha256:"):
            raise InferenceError("artifact_mismatch", 503)
        metadata = self._request("/api/show", {"model": MODEL})
        capabilities = cast(list[str], metadata.get("capabilities", []))
        if not {"completion", "vision"} <= set(capabilities):
            raise InferenceError("artifact_mismatch", 503)

    def _resident(self) -> dict[str, object] | None:
        rows = cast(list[dict[str, object]], self._request("/api/ps").get("models", []))
        return next((row for row in rows if row.get("name") == MODEL), None)

    def unload(self) -> bool:
        self._request(
            "/api/chat", {"model": MODEL, "messages": [], "keep_alive": 0, "stream": False}
        )
        return self._resident() is None

    def recover(self) -> bool:
        # Only a verified stop of our container proves that a timed-out invocation ended.
        return self._recover_owned()

    def _request(
        self, path: str, body: dict[str, object] | None = None, *, timeout: float = 3
    ) -> dict[str, object]:
        operation_deadline = self._budget_state.deadline
        if operation_deadline is not None:
            timeout = min(timeout, operation_deadline - time.monotonic())
        if timeout <= 0:
            raise InferenceError("service_unavailable", 503)
        if self._transport is not None:
            return self._transport(path, body, timeout)
        target = urlsplit(self._settings.endpoint)
        if target.scheme != "http" or target.hostname != "127.0.0.1" or not target.port:
            raise InferenceError("service_unavailable", 503)
        connection = http.client.HTTPConnection("127.0.0.1", target.port, timeout=min(3, timeout))
        started = time.monotonic()
        dispatched = False
        deadline: Timer | None = None
        try:
            connection.connect()
            deadline = Timer(
                max(0.001, timeout - (time.monotonic() - started)),
                _abort_connection,
                args=(connection, connection.sock),
            )
            deadline.start()
            if connection.sock is not None:
                connection.sock.settimeout(timeout)
            dispatched = True
            return _http(connection, path, body, timeout)
        except TimeoutError:
            raise InferenceError(
                "timeout" if path == "/api/chat" else "service_unavailable", 503
            ) from None
        except (OSError, http.client.HTTPException, ValueError):
            code = (
                "execution_unknown" if dispatched and path == "/api/chat" else "service_unavailable"
            )
            raise InferenceError(code, 503) from None
        finally:
            if deadline is not None:
                deadline.cancel()
            connection.close()


def _http(
    connection: http.client.HTTPConnection,
    path: str,
    body: dict[str, object] | None,
    timeout: float,
) -> dict[str, object]:
    deadline = time.monotonic() + timeout
    connection.request(
        "GET" if body is None else "POST",
        path,
        body=json.dumps(body).encode() if body is not None else None,
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    raw = response.read(65537)
    if len(raw) > 65536 or time.monotonic() > deadline:
        raise InferenceError(
            "execution_unknown" if time.monotonic() > deadline else "invalid_output"
        )
    value = json.loads(raw)
    if response.status != 200:
        raise InferenceError(_error_cause(value), 503)
    if not isinstance(value, dict):
        raise InferenceError("invalid_output")
    return cast(dict[str, object], value)


def _error_cause(value: object) -> str:
    message = str(value).lower()
    if "memory" in message or "alloc" in message:
        return "out_of_memory"
    if "not found" in message:
        return "model_missing"
    if any(word in message for word in ["checksum", "corrupt", "tensor"]):
        return "model_corrupt"
    return "service_unavailable"


def _abort_connection(connection: http.client.HTTPConnection, sock: socket.socket | None) -> None:
    if sock is not None:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
    connection.close()


def _metric(value: dict[str, object], key: str) -> int:
    raw = value.get(key)
    if type(raw) is not int or raw < 0 or raw > 2**63 - 1:
        raise InferenceError("invalid_output", diagnostic="invalid_metric_" + key)
    return raw


def _response_metrics(envelope: dict[str, object]) -> dict[str, object]:
    # Duration/count fields are server metadata; generated strings and tool calls are untrusted content.
    return {
        key: value
        for key in [
            "total_duration",
            "load_duration",
            "prompt_eval_duration",
            "eval_duration",
            "prompt_eval_count",
            "eval_count",
        ]
        if type(value := envelope.get(key)) is int and 0 <= value < 2**63
    }


def _resident_metrics(resident: dict[str, object]) -> dict[str, object]:
    return {
        key: value
        for key in ["size", "size_vram", "context_length"]
        if type(value := resident.get(key)) is int and 0 <= value < 2**63
    }


def _residency_before(resident: dict[str, object] | None, expected: str) -> dict[str, object]:
    if resident is None:
        return {"residency_before": "absent"}
    digest = str(resident.get("digest", ""))
    matches = digest.removeprefix("sha256:") == expected.removeprefix("sha256:")
    value: dict[str, object] = {
        "residency_before": "matching_model" if matches else "unverified",
        "resident_before": _resident_metrics(resident),
    }
    if matches:
        value["resident_before_digest"] = expected
    return value


class _CallBudget(local):
    deadline: float | None = None
    service_confirmed: bool = False
