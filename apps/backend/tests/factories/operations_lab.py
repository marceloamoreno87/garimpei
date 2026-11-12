"""Owned, reproducible F17 laboratory. Never loads the operator's environment."""

import argparse
import hashlib
import json
import platform
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from tests.factories.runtime import FoundationInstance, prepare_checkout_copy, prepare_instance

PROFILE = {
    "version": 1,
    "stalled_seconds": 180,
    "tick_seconds": 5,
    "failures": 3,
    "queue_limit": 1000,
    "unit_seconds": 60,
    "archive_seconds": 300,
    "data_bytes": 10 * 1024**3,
    "backup_bytes": 10 * 1024**3,
    "reserve_bytes": 1024**3,
    "backup_interval": 86400,
    "retention": 7,
}


def prepare(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if (directory / "lab.json").exists():
        raise ValueError("Laboratory already prepared")
    root = Path(__file__).resolve().parents[4]
    copy = prepare_checkout_copy(root, directory)
    instances = []
    for role in ("source", "destination"):
        instance = prepare_instance(copy, directory, "f17_" + role + "_" + uuid4().hex[:8])
        with instance.private_file.open("a") as output:
            output.write("GARIMPEI_AI_SERVICE_ENABLED=false\nGARIMPEI_ALERTS_ENABLED=false\n")
            output.write(f"GARIMPEI_BACKUP_DIR={directory / role / 'backups'}\n")
        instances.append({"role": role, "root": str(copy), "file": str(instance.private_file)})
    file = directory / "lab.json"
    file.write_text(json.dumps({"format": 1, "instances": instances}, indent=2) + "\n")
    file.chmod(0o600)


def instances(directory: Path) -> list[FoundationInstance]:
    data = json.loads((directory / "lab.json").read_text())
    return [FoundationInstance(Path(row["root"]), Path(row["file"])) for row in data["instances"]]


def lifecycle(directory: Path, start: bool) -> None:
    for instance in instances(directory):
        result = instance.command(
            "./scripts/init.sh" if start else "./scripts/stop.sh",
            "--disposable" if start else "--clean",
            timeout=180,
        )
        if result.returncode:
            raise RuntimeError("Owned lifecycle failed: " + result.stdout + result.stderr)
    inspect(directory)


def inspect(directory: Path) -> dict[str, object]:
    inventory: list[dict[str, object]] = []
    for instance in instances(directory):
        manifest = instance.manifest
        inventory.append(
            {
                "environment_id": instance.config.environment_id,
                "state": manifest["status"],
                "database": instance.config.database,
                "ports": manifest["ports"],
            }
        )
    result: dict[str, object] = {
        "format_version": 1,
        "instances": inventory,
        "real_services": False,
        "private_files_excluded": True,
    }
    (directory / "fixture-manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def calibrate(directory: Path) -> None:
    from tests.factories.operations_probe import measure_adapters

    source = instances(directory)[0]
    measurements = measure_adapters(source)
    result = {
        "format_version": 1,
        "at": datetime.now(UTC).isoformat(),
        "profile": PROFILE,
        "profile_sha256": hashlib.sha256(json.dumps(PROFILE, sort_keys=True).encode()).hexdigest(),
        "hardware": {"platform": platform.system(), "machine": platform.machine()},
        "python": platform.python_version(),
        "measurements": measurements,
        "free_bytes": shutil.disk_usage(directory).free,
        "scope": "existing adapters with operational timeouts; new stages require later measurement",
        "operational_enablement": False,
    }
    (directory / "calibration.json").write_text(json.dumps(result, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["prepare", "start", "inspect", "calibrate", "close"])
    parser.add_argument("--directory", required=True, type=Path)
    options = parser.parse_args()
    operation, directory = options.operation, options.directory.resolve()
    started = time.monotonic()
    if operation == "prepare":
        prepare(directory)
    elif operation in {"start", "close"}:
        lifecycle(directory, operation == "start")
    elif operation == "calibrate":
        calibrate(directory)
    else:
        inspect(directory)
    print(f"F17 {operation}: completed in {time.monotonic() - started:.2f}s")


if __name__ == "__main__":
    main()
