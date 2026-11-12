import hashlib
import json
import re
from typing import cast

from garimpei.domain.inference.errors import InferenceError
from garimpei.domain.inference.request import MODEL, VERSION

# Deployment and registry pins resolved in the approved F19 artifact preparation.
_IMAGE = (
    "ollama/ollama:0.40.16@sha256:910d0d8107b538fb0894e63163eb195de0cc7aefcbc666dc62d3b18f71124592"
)
_MODEL_DIGEST = "sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04"
_PLATFORM_DIGEST = "sha256:a372a1c0d1e15b68e9521189785c3ca17795c26c2356f8b1b10122cfb59ed0d7"
_TOKENIZER_REPOSITORY = "Qwen/Qwen3.5-4B"
_TOKENIZER_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
_TOKENIZER_SHA256 = "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42"


def validate_artifact_lock(value: object) -> dict[str, object]:
    lock = _mapping(value)
    _require(
        lock,
        {
            "schema_version",
            "image",
            "platform",
            "image_platform_digest",
            "server_version",
            "model",
            "model_digest",
            "manifest",
            "quantization",
            "required_capabilities",
            "tokenizer",
            "prompt_version",
            "schema",
        },
    )
    expected = {
        "schema_version": 1,
        "image": _IMAGE,
        "platform": "linux/amd64",
        "image_platform_digest": _PLATFORM_DIGEST,
        "server_version": "0.40.16",
        "model": MODEL,
        "model_digest": _MODEL_DIGEST,
        "quantization": "Q4_K_M",
        "prompt_version": VERSION,
        "schema": VERSION,
    }
    if any(lock[key] != expected_value for key, expected_value in expected.items()):
        raise InferenceError("artifact_mismatch", 503)
    if lock["required_capabilities"] != ["completion", "vision"]:
        raise InferenceError("artifact_mismatch", 503)
    _manifest(lock["manifest"])
    _tokenizer(lock["tokenizer"])
    return lock


def _mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise InferenceError("artifact_mismatch", 503)
    return cast(dict[str, object], value)


def _require(value: dict[str, object], keys: set[str]) -> None:
    if any(key not in value or value[key] is None or value[key] == "" for key in keys):
        raise InferenceError("artifact_incomplete", 503)


def _manifest(value: object) -> None:
    manifest = _mapping(value)
    _require(manifest, {"schemaVersion", "mediaType", "config", "layers", "runner", "format"})
    layers = manifest["layers"]
    if not isinstance(layers, list):
        raise InferenceError("artifact_mismatch", 503)
    if len(layers) < 5:
        raise InferenceError("artifact_incomplete", 503)
    _descriptor(manifest["config"])
    for layer in layers:
        _descriptor(layer)
    # A syntactically plausible SHA is insufficient: every blob, size and role is
    # bound to the approved registry manifest, including the visual projector.
    try:
        raw = json.dumps(manifest, separators=(",", ":"), ensure_ascii=False).encode()
    except (TypeError, ValueError):
        raise InferenceError("artifact_mismatch", 503) from None
    if "sha256:" + hashlib.sha256(raw).hexdigest() != _MODEL_DIGEST:
        raise InferenceError("artifact_mismatch", 503)


def _descriptor(value: object) -> None:
    descriptor = _mapping(value)
    _require(descriptor, {"mediaType", "digest", "size"})
    size = descriptor["size"]
    if not _sha256(descriptor["digest"], prefix="sha256:"):
        raise InferenceError("artifact_mismatch", 503)
    if type(size) is not int or size <= 0:
        raise InferenceError("artifact_mismatch", 503)


def _tokenizer(value: object) -> None:
    tokenizer = _mapping(value)
    _require(tokenizer, {"repository", "revision", "url", "sha256"})
    expected_url = (
        f"https://huggingface.co/{_TOKENIZER_REPOSITORY}/resolve/"
        f"{_TOKENIZER_REVISION}/tokenizer.json"
    )
    if (
        tokenizer["repository"] != _TOKENIZER_REPOSITORY
        or tokenizer["revision"] != _TOKENIZER_REVISION
        or tokenizer["url"] != expected_url
        or tokenizer["sha256"] != _TOKENIZER_SHA256
    ):
        raise InferenceError("artifact_mismatch", 503)


def _sha256(value: object, *, prefix: str = "") -> bool:
    return isinstance(value, str) and re.fullmatch(prefix + r"[a-f0-9]{64}", value) is not None
