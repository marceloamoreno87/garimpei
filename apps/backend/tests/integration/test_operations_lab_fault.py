"""The F17 fault probe uses only the owned laboratory and retains its checkpoint."""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_persistent_unit_fault_suspends_only_target(tmp_path: Path) -> None:
    backend = Path(__file__).resolve().parents[2]
    directory = tmp_path / "operational-fault"
    environment = dict(os.environ)
    for name in ("DJANGO_SETTINGS_MODULE", "GARIMPEI_ENV_FILE", "VIRTUAL_ENV"):
        environment.pop(name, None)

    def invoke(operation: str, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "tests.factories.operations_lab",
                operation,
                "--directory",
                str(directory),
                *arguments,
            ],
            cwd=backend,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )

    prepared = invoke("prepare")
    assert prepared.returncode == 0, prepared.stderr
    try:
        for operation, arguments in (("start", ()), ("seed", ("--scenario", "recovery"))):
            result = invoke(operation, *arguments)
            assert result.returncode == 0, result.stdout + result.stderr
        result = invoke("fault", "--case", "unit_persistent")
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads((directory / "fault-unit_persistent.json").read_text())
        assert report["target"] == {"suspended": True, "failures": 3, "checkpoint": "confirmed-A"}
        assert report["control"] == {"suspended": False, "failures": 0, "checkpoint": "confirmed-B"}
        assert report["seconds"] >= 0
        repeated = invoke("fault", "--case", "unit_persistent")
        assert repeated.returncode != 0
    finally:
        closed = invoke("close")
        assert closed.returncode == 0, closed.stdout + closed.stderr
