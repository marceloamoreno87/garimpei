"""Calibrate existing stages and sample both owned instances, including private media/backups."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from tests.factories.operations_lab import instances, lifecycle, prepare, seed
from tests.factories.operations_metrics import InstanceMeasurements


def run(directory: Path) -> None:
    prepare(directory)
    try:
        lifecycle(directory, True)
        seed(directory, "backup")
        source, target = instances(directory)
        with (
            InstanceMeasurements(
                source, directory / "source-resources.json", mode="fault"
            ),
            InstanceMeasurements(
                target, directory / "target-resources.json", mode="fault"
            ),
        ):
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tests.factories.operations_lab",
                    "calibrate",
                    "--directory",
                    str(directory),
                ],
                capture_output=True,
                text=True,
                timeout=750,
            )
            (directory / "calibrate-private.log").write_text(
                result.stdout + result.stderr
            )
            assert result.returncode == 0, (
                "Canonical calibration failed; inspect private log"
            )
        observed = json.loads((directory / "calibration.json").read_text())
        observed["resource_measurements"] = {
            role: json.loads((directory / filename).read_text())
            for role, filename in (
                ("source", "source-resources.json"),
                ("destination", "target-resources.json"),
            )
        }
        observed["resource_scope"] = (
            "Full canonical adapter/fault/backup/export/restore/reconciliation run; logical-byte peaks sampled at 0.1s; unavailable samples counted explicitly"
        )
        observed["pending"] = [
            "Consolidate paired cuts and mixed-load isolation before confirming the unchanged profile"
        ]
        (directory / "calibration-instrumented.json").write_text(
            json.dumps(observed, indent=2) + "\n"
        )
    finally:
        lifecycle(directory, False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    run(parser.parse_args().directory.resolve())
