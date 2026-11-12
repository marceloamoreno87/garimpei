import json
import subprocess

from garimpei.config.env import RuntimeConfig, process_environment
from garimpei.infra.runtime.manifest import OperationError


def docker(arguments: list[str], config: RuntimeConfig, *, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            ["docker", *arguments],
            cwd=config.root,
            env=process_environment(config, config.run_id),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise OperationError("Docker: unavailable or operation timeout") from None
    if result.returncode:
        raise OperationError(
            "Docker: operation failed; check daemon, image digest and owned resources"
        )
    return result.stdout.strip()


def compose(config: RuntimeConfig, arguments: list[str]) -> str:
    return docker(
        [
            "compose",
            "-p",
            "garimpei-" + config.environment_id,
            "-f",
            str(config.root / "compose.yaml"),
            *arguments,
        ],
        config,
        timeout=config.startup_timeout,
    )


def container_ids(config: RuntimeConfig) -> list[str]:
    output = docker(
        ["ps", "-aq", "--filter", "label=com.garimpei.environment=" + config.environment_id], config
    )
    return output.splitlines() if output else []


def verify_container(identifier: str, config: RuntimeConfig) -> None:
    labels = json.loads(
        docker(["inspect", "--format", "{{json .Config.Labels}}", identifier], config)
    )
    if labels.get("com.garimpei.environment") != config.environment_id or labels.get(
        "com.garimpei.checkout"
    ) != str(config.root):
        raise OperationError("Container ownership: marker/checkout mismatch")


def running_containers(config: RuntimeConfig) -> set[str]:
    output = docker(
        ["ps", "-q", "--filter", "label=com.garimpei.environment=" + config.environment_id], config
    )
    return set(output.splitlines()) if output else set()


def stop_containers(config: RuntimeConfig, identifiers: list[str]) -> None:
    for identifier in identifiers:
        verify_container(identifier, config)
    if identifiers:
        docker(
            ["stop", "--time", str(config.shutdown_timeout), *identifiers],
            config,
            timeout=config.shutdown_timeout + 10,
        )


def network_ids(config: RuntimeConfig) -> list[str]:
    project = "garimpei-" + config.environment_id
    output = docker(
        ["network", "ls", "-q", "--filter", "label=com.docker.compose.project=" + project], config
    )
    return output.splitlines() if output else []


def verify_network(identifier: str, config: RuntimeConfig, containers: list[str]) -> None:
    data = json.loads(docker(["network", "inspect", "--format", "{{json .}}", identifier], config))
    labels = data.get("Labels") or {}
    if labels.get("com.garimpei.environment") != config.environment_id or labels.get(
        "com.garimpei.checkout"
    ) != str(config.root):
        raise OperationError("Network ownership: marker/checkout mismatch")
    if labels.get("com.docker.compose.project") != "garimpei-" + config.environment_id:
        raise OperationError("Network ownership: Compose project mismatch")
    attached = data.get("Containers") or {}
    if any(not any(endpoint.startswith(owned) for owned in containers) for endpoint in attached):
        raise OperationError("Network ownership: foreign endpoints attached; refusing cleanup")
