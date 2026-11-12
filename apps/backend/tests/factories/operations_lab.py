"""Owned, reproducible F17 laboratory. Never loads the operator's environment."""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import psutil

from tests.factories.runtime import (
    FoundationInstance,
    pause_worker,
    prepare_checkout_copy,
    prepare_instance,
    resume_worker,
)

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
            output.write(
                f"GARIMPEI_MEDIA_ROOT={directory / role / 'media'}\nGARIMPEI_MEDIA_BUDGET_BYTES=67108864\nGARIMPEI_MEDIA_MAX_FILE_BYTES=1048576\n"
            )
            output.write(
                f"GARIMPEI_LISTING_FIXTURE_URL=http://127.0.0.1:9\nGARIMPEI_LISTING_FIXTURE_CLOCK={directory / 'clock'}\n"
            )
        instances.append({"role": role, "root": str(copy), "file": str(instance.private_file)})
    (directory / "clock").write_text(datetime.now(UTC).replace(microsecond=0).isoformat())
    file = directory / "lab.json"
    file.write_text(json.dumps({"format": 1, "instances": instances}, indent=2) + "\n")
    file.chmod(0o600)


def instances(directory: Path) -> list[FoundationInstance]:
    data = json.loads((directory / "lab.json").read_text())
    if [row["role"] for row in data["instances"]] != ["source", "destination"]:
        raise ValueError("Expected source and destination owned laboratory instances")
    result = [FoundationInstance(Path(row["root"]), Path(row["file"])) for row in data["instances"]]
    for instance in result:
        if (
            instance.root != directory / "checkout"
            or instance.root.is_symlink()
            or instance.private_file.parent != directory
            or instance.private_file.is_symlink()
            or instance.config.environment != "eval"
        ):
            raise ValueError("Laboratory ownership mismatch")
    return result


def lifecycle(directory: Path, start: bool) -> None:
    if not start:
        _resume_owned(directory)
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
        manifest_file = instance.config.directory / "manifest.json"
        manifest = instance.manifest if manifest_file.exists() else None
        live = _owned_processes(instance)
        containers = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                f"label=com.docker.compose.project=garimpei-{instance.config.environment_id}",
                "--format",
                "{{.ID}}",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        if manifest is None and (live or containers):
            raise RuntimeError("Owned resources remain without a lifecycle manifest")
        inventory.append(
            {
                "environment_id": instance.config.environment_id,
                "state": manifest["status"] if manifest else "closed",
                "database": instance.config.database,
                "ports": manifest["ports"] if manifest else {},
                "live_processes": live,
                "owned_containers": len(containers),
            }
        )
    result: dict[str, object] = {
        "format_version": 1,
        "instances": inventory,
        "real_services": False,
        "private_files_excluded": True,
        "corpus": json.loads((directory / "seed-report.json").read_text())
        if (directory / "seed-report.json").exists()
        else None,
    }
    (directory / "fixture-manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def _owned_processes(instance: FoundationInstance) -> list[int]:
    result = []
    for process in psutil.process_iter(["pid", "cwd", "cmdline"]):
        try:
            command = process.info["cmdline"] or []
            if (
                process.info["cwd"] == str(instance.root / "apps/backend")
                and ("runworker" in command or "gunicorn" in command)
                and process.environ().get("GARIMPEI_ENV_FILE") == str(instance.private_file)
            ):
                result.append(process.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return result


def _resume_owned(directory: Path) -> None:
    data = json.loads((directory / "lab.json").read_text())
    paused = data.get("paused_source")
    if not paused:
        return
    source = instances(directory)[0]
    from garimpei.infra.runtime.processes import verify_process

    manifest = source.manifest
    owner = next(row for row in manifest["processes"] if row["pgid"] == paused["pgid"])
    if manifest["run_id"] != paused["run_id"]:
        raise ValueError("Paused source owner changed")
    verify_process(owner, source.root)
    resume_worker(owner["pgid"])
    del data["paused_source"]
    (directory / "lab.json").write_text(json.dumps(data, indent=2) + "\n")


def seed(directory: Path, scenario: str) -> None:
    from tests.factories.alert import WahaServer, serve_waha
    from tests.factories.media import serve_media

    source = instances(directory)[0]
    data = json.loads((directory / "lab.json").read_text())
    if data.get("paused_source"):
        raise ValueError("A seeded source already exists; prepare a fresh owned laboratory")
    group = pause_worker(source)
    channel = WahaServer(recipient="100@g.us")
    try:
        with serve_waha(channel) as url, serve_media() as (origin, requests):
            with source.private_file.open("a") as output:
                output.write(f"GARIMPEI_MEDIA_EVAL_ORIGIN={origin}\n")
            result = source.shell(
                "import json;from pathlib import Path;from tests.factories.operations_lab_seed import seed_counts,seed_protected_photo;"
                f"value=seed_counts({url!r});value['protected_photo']=seed_protected_photo({origin!r});Path({str(directory / 'seed-report.json')!r}).write_text(json.dumps(value,indent=2)+'\\n')"
            )
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            history = directory / "channel-messages.json"
            history.write_text(json.dumps(channel.messages, indent=2) + "\n")
            history.chmod(0o600)
        assert len(channel.messages) == 2
        assert len(requests) == 1
    except BaseException:
        resume_worker(group)
        raise
    data["paused_source"] = {"pgid": group, "run_id": source.manifest["run_id"]}
    (directory / "lab.json").write_text(json.dumps(data, indent=2) + "\n")
    if scenario in {"recovery", "backup"}:
        result = source.shell(
            "from tests.factories.operations_lab_seed import seed_recovery;seed_recovery()"
        )
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
    if scenario == "backup":
        result = source.shell(
            "from tests.factories.operations_lab_seed import seed_backup_choice;seed_backup_choice()"
        )
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        _credential_canaries(directory)
    data["scenario"] = scenario
    (directory / "lab.json").write_text(json.dumps(data, indent=2) + "\n")
    inspect(directory)


def _credential_canaries(directory: Path) -> None:
    folder = directory / "private-canaries"
    folder.mkdir(mode=0o700)
    values = {}
    for name in ("cookies", "profile", "session-waha", "qr", "environment", "authorization"):
        value = "synthetic-" + uuid4().hex
        path = folder / name
        path.write_text(value)
        path.chmod(0o600)
        values[name] = value
    manifest = directory / "canaries.json"
    manifest.write_text(json.dumps(values) + "\n")
    manifest.chmod(0o600)


def calibrate(directory: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    from tests.factories.operations_lab_calibration import measure_new_stages
    from tests.factories.operations_probe import measure_adapters

    source, target = instances(directory)
    if (
        not (directory / "channel-messages.json").exists()
        or not (directory / "canaries.json").exists()
    ):
        raise ValueError(
            "Calibration requires the owned backup scenario and retained fake provider history"
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        adapters = pool.submit(measure_adapters, source)
        stages = pool.submit(measure_new_stages, directory, source, target)
        measurements, new_stages = adapters.result(), stages.result()
    result = {
        "format_version": 1,
        "at": datetime.now(UTC).isoformat(),
        "profile": PROFILE,
        "profile_sha256": hashlib.sha256(json.dumps(PROFILE, sort_keys=True).encode()).hexdigest(),
        "hardware": {"platform": platform.system(), "machine": platform.machine()},
        "python": platform.python_version(),
        "measurements": measurements,
        "new_stage_measurements": new_stages,
        "free_bytes": shutil.disk_usage(directory).free,
        "scope": "operational adapter timeouts and five controls of owned backup/export/restore/verified reconciliation",
        "pending": [
            "full fault CLI matrix is not yet implemented; real enablement remains blocked"
        ],
        "operational_enablement": False,
    }
    (directory / "calibration.json").write_text(json.dumps(result, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation", choices=["prepare", "start", "seed", "inspect", "calibrate", "close"]
    )
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument(
        "--scenario", choices=["healthy", "counts", "recovery", "backup"], default="counts"
    )
    options = parser.parse_args()
    operation, directory = options.operation, options.directory.resolve()
    started = time.monotonic()
    if operation == "prepare":
        prepare(directory)
    elif operation in {"start", "close"}:
        lifecycle(directory, operation == "start")
    elif operation == "calibrate":
        calibrate(directory)
    elif operation == "seed":
        seed(directory, options.scenario)
    else:
        inspect(directory)
    print(f"F17 {operation}: completed in {time.monotonic() - started:.2f}s")


if __name__ == "__main__":
    main()
