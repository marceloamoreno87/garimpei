import json
import subprocess

from garimpei.config.env import RuntimeConfig, process_environment
from garimpei.infra.runtime.deadline import remaining
from garimpei.infra.runtime.manifest import OperationError


def docker(arguments: list[str], config: RuntimeConfig, *, timeout: float = 30) -> str:
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


def compose(config: RuntimeConfig, arguments: list[str], *, timeout: float | None = None) -> str:
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
        timeout=config.startup_timeout if timeout is None else timeout,
    )


def container_ids(config: RuntimeConfig, *, timeout: float = 30) -> list[str]:
    output = docker(
        ["ps", "-aq", "--filter", "label=com.garimpei.environment=" + config.environment_id],
        config,
        timeout=timeout,
    )
    return output.splitlines() if output else []


def verify_container(identifier: str, config: RuntimeConfig, *, timeout: float = 30) -> None:
    labels = json.loads(
        docker(
            ["inspect", "--format", "{{json .Config.Labels}}", identifier], config, timeout=timeout
        )
    )
    if labels.get("com.garimpei.environment") != config.environment_id or labels.get(
        "com.garimpei.checkout"
    ) != str(config.root):
        raise OperationError("Container ownership: marker/checkout mismatch")


def running_containers(config: RuntimeConfig, *, timeout: float = 30) -> set[str]:
    output = docker(
        ["ps", "-q", "--filter", "label=com.garimpei.environment=" + config.environment_id],
        config,
        timeout=timeout,
    )
    return set(output.splitlines()) if output else set()


def stop_containers(
    config: RuntimeConfig, identifiers: list[str], *, deadline: float | None = None
) -> None:
    for identifier in identifiers:
        verify_container(identifier, config, timeout=remaining(deadline))
    if identifiers:
        grace = config.shutdown_timeout
        if deadline is not None:
            grace = min(grace, max(0, int(remaining(deadline) - 0.2)))
        docker(
            ["stop", "--time", str(grace), *identifiers],
            config,
            timeout=remaining(deadline, maximum=config.shutdown_timeout + 10),
        )


def network_ids(config: RuntimeConfig, *, timeout: float = 30) -> list[str]:
    project = "garimpei-" + config.environment_id
    output = docker(
        ["network", "ls", "-q", "--filter", "label=com.docker.compose.project=" + project],
        config,
        timeout=timeout,
    )
    return output.splitlines() if output else []


def verify_network(
    identifier: str, config: RuntimeConfig, containers: list[str], *, timeout: float = 30
) -> None:
    data = json.loads(
        docker(
            ["network", "inspect", "--format", "{{json .}}", identifier], config, timeout=timeout
        )
    )
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
