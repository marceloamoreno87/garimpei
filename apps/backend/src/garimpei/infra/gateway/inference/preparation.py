import hashlib
import json
import urllib.request
from pathlib import Path
from typing import cast

from garimpei.config.env import InferenceSettings, RuntimeConfig
from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.gateway.inference.input_preparer import read_lock
from garimpei.infra.gateway.inference.ollama_gateway import OllamaGateway
from garimpei.infra.runtime.containers import docker
from garimpei.infra.runtime.inference_runtime import owned_model_container


def prepare_download(
    config: RuntimeConfig, settings: InferenceSettings, gateway: OllamaGateway
) -> None:
    gateway.diagnose()  # Warm the owned persistent bridge while artifacts are prepared.
    lock = read_lock(settings.model_lock)
    image = str(lock.get("image", ""))
    if not image.startswith("ollama/ollama:") or "@sha256:" not in image or "latest" in image:
        raise InferenceError("artifact_mismatch", 503)
    identifier = owned_model_container(config)
    if identifier is None:
        raise InferenceError("service_unavailable", 503)
    # External connectivity exists only during explicit artifact preparation.
    networks = json.loads(
        docker(["inspect", "--format", "{{json .NetworkSettings.Networks}}", identifier], config)
    )
    network = "garimpei-" + config.environment_id + "_default"
    already = network in networks
    try:
        if not already:
            docker(["network", "connect", network, identifier], config)
        docker(["exec", identifier, "ollama", "pull", str(lock["model"])], config, timeout=1200)
        _tokenizer(settings, lock)
    finally:
        if not already:
            docker(["network", "disconnect", network, identifier], config)
    _verify_blobs(config, identifier, lock)
    diagnostic = gateway.diagnose()
    if diagnostic["reason"] != "ready":
        raise InferenceError(str(diagnostic["reason"]), 503)


def _tokenizer(settings: InferenceSettings, lock: dict[str, object]) -> None:
    metadata = cast(dict[str, str], lock["tokenizer"])
    url = metadata["url"]
    prefix = "https://huggingface.co/Qwen/Qwen3.5-4B/resolve/"
    if not url.startswith(prefix) or not url.endswith("/tokenizer.json"):
        raise InferenceError("artifact_mismatch", 503)
    with urllib.request.urlopen(url, timeout=60) as response:
        raw = response.read(20000001)
    if len(raw) > 20000000 or hashlib.sha256(raw).hexdigest() != metadata["sha256"]:
        raise InferenceError("artifact_mismatch", 503)
    settings.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = settings.tokenizer.with_suffix(".tmp")
    temporary.write_bytes(raw)
    temporary.chmod(0o600)
    temporary.replace(settings.tokenizer)


def _verify_blobs(config: RuntimeConfig, identifier: str, lock: dict[str, object]) -> None:
    manifest = cast(dict[str, object], lock["manifest"])
    layers = [
        cast(dict[str, str], manifest["config"]),
        *cast(list[dict[str, str]], manifest["layers"]),
    ]
    for layer in layers:
        digest = layer["digest"]
        if len(digest) != 71 or not digest.startswith("sha256:"):
            raise InferenceError("artifact_mismatch", 503)
        path = "/root/.ollama/models/blobs/" + digest.replace(":", "-")
        actual = docker(["exec", identifier, "sha256sum", path], config, timeout=120).split()[0]
        if actual != digest.removeprefix("sha256:"):
            raise InferenceError("model_corrupt", 503)
    repo = docker(["inspect", "--format", "{{.Config.Image}}", identifier], config)
    if repo != lock["image"]:
        raise InferenceError("artifact_mismatch", 503)


def register_corpus(config: RuntimeConfig, settings: InferenceSettings) -> None:
    from garimpei.infra.gateway.inference.registry import register_file

    corpus = config.root / "apps/backend/tests/fixtures/inference"
    values = json.loads((corpus / "cases.json").read_text())
    for identity, metadata in values["images"].items():
        register_file(settings, corpus / (identity + ".png"), metadata)
    if settings.photo_manifest is not None:
        metadata = json.loads(settings.photo_manifest.read_text())
        register_file(settings, Path(metadata["path"]), metadata)


def calibrate_visual(settings: InferenceSettings, gateway: OllamaGateway) -> None:
    from garimpei.domain.inference.ports import PreparedPart
    from garimpei.domain.inference.result import validate_result
    from garimpei.infra.gateway.inference.input_preparer import LocalInputPreparer, image_derivative
    from garimpei.infra.gateway.inference.registry import registered

    metadata = registered(settings, "image-a")
    raw = (settings.directory / "sources" / str(metadata["sha256"])).read_bytes()
    derivative = image_derivative(raw)
    digest = hashlib.sha256(derivative).hexdigest()
    preparer = LocalInputPreparer(settings)
    preparer._store(digest, derivative)
    result = gateway.infer(PreparedPart("calibration", "", "image-a", digest), preparer.artifact())
    validate_result(str(result["content"]), "", ("image-a",))
    lock = read_lock(settings.model_lock)
    lock["visual_context_verified"] = True
    lock["visual_profile"] = {
        "max_derivative": [512, 512],
        "one_image_per_call": True,
        "metrics": result["metrics"],
        "schema": "bounded-references-v1",
    }
    settings.model_lock.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n")
