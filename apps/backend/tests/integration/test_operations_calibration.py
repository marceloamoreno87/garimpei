"""The documented F17 command runs outside Django and owns its complete cleanup."""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_direct_calibration_keeps_five_recovery_controls_and_closes_clean_destination(
    tmp_path: Path,
) -> None:
    backend = Path(__file__).resolve().parents[2]
    directory = tmp_path / "operational-calibration"
    environment = dict(os.environ)
    environment.pop("DJANGO_SETTINGS_MODULE", None)
    environment.pop("GARIMPEI_ENV_FILE", None)
    environment.pop("VIRTUAL_ENV", None)

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
            text=True,
            capture_output=True,
            timeout=600,
        )

    prepared = invoke("prepare")
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr
    try:
        started = invoke("start")
        assert started.returncode == 0, started.stdout + started.stderr
        seeded = invoke("seed", "--scenario", "backup")
        assert seeded.returncode == 0, seeded.stdout + seeded.stderr
        calibrated = invoke("calibrate")
        assert calibrated.returncode == 0, calibrated.stdout + calibrated.stderr
        report = json.loads((directory / "calibration.json").read_text())
        assert report["operational_enablement"] is False
        assert report["profile_confirmed"] is False and report["pending"]
        fault_measurements = report["fault_measurements"]
        assert len(fault_measurements) == 35
        assert {row["repetition"] for row in fault_measurements} == {1, 2, 3, 4, 5}
        measurements = report["measurements"]
        for stage in ("source", "valuation", "channel"):
            for case in ("control", "timeout"):
                selected = [
                    row for row in measurements if (row["stage"], row["case"]) == (stage, case)
                ]
                assert {row["repetition"] for row in selected} == {1, 2, 3, 4, 5}
        controls = report["new_stage_measurements"]
        assert len(controls) == 5 and {row["repetition"] for row in controls} == {1, 2, 3, 4, 5}
        assert all(
            row["restoration_state"] == "verified"
            and row["duplicate_posts"] == 0
            and row["private_input_scan"] == "passed"
            and row["protected_originals"] == 1
            for row in controls
        )
    finally:
        closed = invoke("close")
        assert closed.returncode == 0, closed.stdout + closed.stderr
    closed_again = invoke("close")
    assert closed_again.returncode == 0, closed_again.stdout + closed_again.stderr
    inventory = json.loads((directory / "fixture-manifest.json").read_text())
    assert all(
        row["state"] == "closed"
        and not row["live_processes"]
        and row["owned_containers"] == 0
        and row["owned_networks"] == 0
        and row["owned_volumes"] == 0
        for row in inventory["instances"]
    )
