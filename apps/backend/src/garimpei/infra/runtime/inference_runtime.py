import json
import time

from garimpei.config.env import InferenceSettings, RuntimeConfig, load_inference_settings
from garimpei.domain.inference.errors import InferenceError
from garimpei.infra.gateway.inference.gpu_guard import HostGpuGuard
from garimpei.infra.runtime.containers import compose, docker, verify_container
from garimpei.infra.runtime.manifest import OperationError


def owned_model_container(config: RuntimeConfig, *, timeout: float = 30) -> str | None:
    deadline = time.monotonic() + timeout
    output = docker(
        [
            "ps",
            "-aq",
            "--filter",
            "label=com.garimpei.environment=" + config.environment_id,
            "--filter",
            "label=com.docker.compose.service=ollama",
        ],
        config,
        timeout=timeout,
    )
    identifiers = output.splitlines()
    if len(identifiers) > 1:
        raise OperationError("AI: expected one owned model container")
    if not identifiers:
        return None
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise OperationError("AI ownership check exceeded deadline")
    verify_container(identifiers[0], config, timeout=remaining)
    return identifiers[0]


def start_inference_service(
    config: RuntimeConfig, settings: InferenceSettings, guard: HostGpuGuard
) -> str:
    if not guard.reserve():
        raise InferenceError("gpu_unavailable", 503)
    compose(config, ["--profile", "ai", "up", "-d", "--pull", "never", "ollama"])
    identifier = owned_model_container(config)
    if identifier is None:
        raise InferenceError("service_unavailable", 503)
    return identifier


def recover_inference_service(config: RuntimeConfig, guard: HostGpuGuard) -> bool:
    if not guard.owned():
        return False
    identifier = owned_model_container(config)
    if identifier is None:
        return True
    docker(["stop", "--time", "3", identifier], config)
    state = json.loads(docker(["inspect", "--format", "{{json .State}}", identifier], config))
    if state.get("Running"):
        return False
    # A new container execution cannot retain the former in-flight inference.
    docker(["start", identifier], config)
    return True


def release_inference_service(config: RuntimeConfig, guard: HostGpuGuard) -> None:
    identifier = owned_model_container(config)
    if identifier:
        state = json.loads(docker(["inspect", "--format", "{{json .State}}", identifier], config))
        if state.get("Running"):
            raise OperationError("AI: reservation retained while owned container is running")
    guard.release()


def release_configured_inference(config: RuntimeConfig) -> None:
    # Shutdown must work without Django/DB/secrets, including a failed or already stopped start.
    settings = load_inference_settings()
    guard = HostGpuGuard(settings.gpu_lock, settings.owner)
    if guard.owned():
        release_inference_service(config, guard)
