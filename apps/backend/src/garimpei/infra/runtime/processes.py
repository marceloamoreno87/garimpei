import os
import signal
import subprocess
import time
from pathlib import Path

import psutil

from garimpei.infra.runtime.manifest import OperationError, ProcessRecord


def start_process(
    command: list[str], cwd: Path, environ: dict[str, str], logfile: Path
) -> ProcessRecord:
    with logfile.open("a") as output:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environ,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=output,
            start_new_session=True,
        )
    logfile.chmod(0o600)
    return {
        "pid": process.pid,
        "pgid": os.getpgid(process.pid),
        "created": psutil.Process(process.pid).create_time(),
        "command": command,
        "cwd": str(cwd),
    }


def is_live(record: ProcessRecord) -> bool:
    try:
        process = psutil.Process(record["pid"])
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def verify_process(record: ProcessRecord, root: Path) -> None:
    if not is_live(record):
        return
    process = psutil.Process(record["pid"])
    expected_cwd = root / "apps/backend"
    if record["cwd"] != str(expected_cwd) or process.cwd() != str(expected_cwd):
        raise OperationError("Process ownership: checkout/cwd mismatch")
    if (
        abs(process.create_time() - record["created"]) > 0.01
        or os.getpgid(process.pid) != record["pgid"]
    ):
        raise OperationError("Process ownership: PID was reused or group differs")
    if process.cmdline() != record["command"] or record["pgid"] != record["pid"]:
        raise OperationError("Process ownership: command/group mismatch")


def stop_process(record: ProcessRecord, root: Path, timeout: float) -> bool:
    verify_process(record, root)
    if not is_live(record):
        return True
    os.killpg(record["pgid"], signal.SIGTERM)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and is_live(record):
        time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    if is_live(record):
        verify_process(record, root)
        os.killpg(record["pgid"], signal.SIGKILL)
        return False
    return True
