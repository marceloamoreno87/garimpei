import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest

from tests.factories.runtime import prepare_checkout_copy, prepare_instance


@pytest.mark.parametrize("fault", ["postgres", "waha", "image"])
def test_real_unavailable_service_or_image_refuses_start_and_rolls_back(
    tmp_path: Path, fault: str
) -> None:
    root = Path(__file__).resolve().parents[4]
    copy = prepare_checkout_copy(root, tmp_path)
    instance = prepare_instance(copy, tmp_path, "fault_" + uuid.uuid4().hex[:10])
    compose = copy / "compose.yaml"
    text = compose.read_text()
    if fault == "postgres":
        text = text.replace(
            "${POSTGRES_PASSWORD:?private password required}", "technical-mismatch-canary"
        )
    elif fault == "waha":
        text = text.replace(
            "${WAHA_API_KEY:?private API key required}", "technical-mismatch-canary"
        )
    else:
        text = text.replace(
            "ff87138949ad9a46f32ff23bd6852b52ce024a13dffe9b4087be98292cdd3b4f", "0" * 64
        )
    compose.write_text(text)
    with instance.private_file.open("a") as file:
        file.write("GARIMPEI_STARTUP_TIMEOUT_SECONDS=8\nGARIMPEI_SHUTDOWN_TIMEOUT_SECONDS=1\n")
    started = time.monotonic()
    try:
        result = instance.command("./scripts/init.sh", "--disposable")
        assert result.returncode == 1, result.stdout + result.stderr
        elapsed = time.monotonic() - started
        print(f"{fault} startup including rollback: {elapsed:.6f}s")
        assert elapsed <= 8
        assert "Ready" not in result.stdout
        assert "technical-mismatch-canary" not in result.stdout + result.stderr
        running = instance.command(
            "docker",
            "ps",
            "-q",
            "--filter",
            "label=com.garimpei.environment=" + instance.config.environment_id,
        )
        assert not running.stdout.strip()
    finally:
        # A failed image may never create a WAHA container to inspect. Delete only
        # resources created by this fresh, explicitly disposable fixture, after label checks.
        config = instance.config
        identifiers = instance.command(
            "docker",
            "ps",
            "-aq",
            "--filter",
            "label=com.garimpei.environment=" + config.environment_id,
        ).stdout.split()
        for identifier in identifiers:
            labels = json.loads(
                instance.command(
                    "docker", "inspect", "--format", "{{json .Config.Labels}}", identifier
                ).stdout
            )
            assert labels["com.garimpei.checkout"] == str(copy)
            assert instance.command("docker", "rm", "-f", identifier).returncode == 0
        volumes = instance.command(
            "docker",
            "volume",
            "ls",
            "-q",
            "--filter",
            "label=com.garimpei.environment=" + config.environment_id,
        ).stdout.split()
        for volume in volumes:
            labels = json.loads(
                instance.command(
                    "docker", "volume", "inspect", "--format", "{{json .Labels}}", volume
                ).stdout
            )
            assert labels["com.garimpei.checkout"] == str(copy)
            assert instance.command("docker", "volume", "rm", volume).returncode == 0

        networks = instance.command(
            "docker",
            "network",
            "ls",
            "-q",
            "--filter",
            "label=com.garimpei.environment=" + config.environment_id,
        ).stdout.split()
        for network in networks:
            data = json.loads(instance.command("docker", "network", "inspect", network).stdout)[0]
            assert data["Labels"]["com.garimpei.checkout"] == str(copy)
            assert not data["Containers"]
            assert instance.command("docker", "network", "rm", network).returncode == 0


@pytest.mark.parametrize("missing", ["uv", "docker", "git", "node", "python"])
def test_missing_system_tool_is_not_installed(tmp_path: Path, missing: str) -> None:
    root = Path(__file__).resolve().parents[4]
    instance = prepare_instance(root, tmp_path, "missing_tool")
    bin_directory = tmp_path / "bin"
    bin_directory.mkdir()
    tools = [
        tool
        for tool in ("dirname", "git", "node", "uv")
        if tool != missing and not (missing == "python" and tool == "uv")
    ]
    for tool in tools:
        original = shutil.which(tool)
        assert original is not None
        (bin_directory / tool).symlink_to(original)
    if missing == "python":
        (bin_directory / "uv").write_text("#!/bin/sh\nexit 1\n")
        (bin_directory / "uv").chmod(0o755)
    environment = instance.environment | {"PATH": str(bin_directory)}
    bash = shutil.which("bash")
    assert bash is not None
    result = subprocess.run(
        [bash, "scripts/init.sh"], cwd=root, env=environment, capture_output=True, text=True
    )
    assert result.returncode == 64
    assert missing in result.stderr.lower()
    assert "Ready" not in result.stdout
