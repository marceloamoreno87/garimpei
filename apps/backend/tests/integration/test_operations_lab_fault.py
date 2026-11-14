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
            # Five sequential pairs each retain their own 150-second deadline.
            timeout=5 * 150 + 30 if operation == "calibrate-crashes" else 180,
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
        for case in ("disk_full", "archive_interrupted", "export_interrupted"):
            result = invoke("fault", "--case", case)
            assert result.returncode == 0, result.stdout + result.stderr
            report = json.loads((directory / f"fault-{case}.json").read_text())
            assert report["control"]["completed"] is True
            assert report["fault"]["rejected"] is True
            assert report["fault"]["previous_preserved"] is True
            assert report["fault"]["no_partial"] is True
            assert report["seconds"] >= 0
        queued = invoke("fault", "--case", "queue_full")
        assert queued.returncode == 0, queued.stdout + queued.stderr
        report = json.loads((directory / "fault-queue_full.json").read_text())
        assert report["control"]["admitted"] is True
        assert report["fault"]["admitted"] is False
        assert report["fault"]["pending"] == 1000
        assert report["cleaned"] is True
        for case in ("network_timeout", "slow_valuation", "slow_channel"):
            result = invoke("fault", "--case", case)
            assert result.returncode == 0, result.stdout + result.stderr
            report = json.loads((directory / f"fault-{case}.json").read_text())
            assert report["control"]["outcome"] == "success"
            assert report["fault"]["outcome"] == (
                "uncertain" if case == "slow_channel" else "timeout"
            )
            assert report["timeout_seconds"] == 1
        for case in ("repeat_cursor", "lease_expired", "late_result", "crash_before_commit"):
            result = invoke("fault", "--case", case)
            assert result.returncode == 0, result.stdout + result.stderr
            report = json.loads((directory / f"fault-{case}.json").read_text())
            assert report["fault_detected"] is True
            assert report["control_confirmed"] is True
            assert report["seed_preserved"] is True
        unavailable = invoke("fault", "--case", "db_unavailable")
        assert unavailable.returncode == 0, unavailable.stdout + unavailable.stderr
        report = json.loads((directory / "fault-db_unavailable.json").read_text())
        assert report["fault"]["unavailable"] is True
        assert report["control"]["source_available"] is True
        assert report["recovered"] is True
        measured = invoke("calibrate-faults")
        assert measured.returncode == 0, measured.stdout + measured.stderr
        report = json.loads((directory / "fault-calibration.json").read_text())
        assert report["profile_confirmed"] is False
        assert report["operational_enablement"] is False
        for case in (
            "network_timeout",
            "slow_valuation",
            "slow_channel",
            "disk_full",
            "archive_interrupted",
            "export_interrupted",
            "queue_full",
        ):
            rows = [row for row in report["measurements"] if row["case"] == case]
            assert {row["repetition"] for row in rows} == {1, 2, 3, 4, 5}
            assert all(row["control"] and row["fault"] for row in rows)
            assert all(row["disk_free_bytes"] > 0 for row in rows)
        for case in ("crash_after_post", "crash_after_commit"):
            result = invoke("fault", "--case", case)
            assert result.returncode == 0, result.stdout + result.stderr
            report = json.loads((directory / f"fault-{case}.json").read_text())
            assert report["fault_detected"] is True
            assert report["recovered"] is True
            assert report["real_sigkill"] is True
        repeated_crashes = invoke("calibrate-crashes", "--repetitions", "1")
        assert repeated_crashes.returncode == 0, repeated_crashes.stdout + repeated_crashes.stderr
        report = json.loads((directory / "crash-calibration.json").read_text())
        assert len(report["measurements"]) == 5
        assert {row["case"] for row in report["measurements"]} == {
            "crash_after_post",
            "crash_after_commit",
            "crash_after_authorization",
            "crash_after_confirmation",
            "crash_before_authorization",
        }
        assert all(row["real_sigkill"] and row["recovered"] for row in report["measurements"])
        assert report["profile_confirmed"] is False
    finally:
        closed = invoke("close")
        assert closed.returncode == 0, closed.stdout + closed.stderr
