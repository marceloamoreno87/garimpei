"""Each queue owns one process/slot; children remain in the lifecycle's owned group."""

import signal
import subprocess
import sys
from pathlib import Path
from threading import Event

QUEUES = ("runtime", "listing", "valuation", "alert", "inference", "maintenance", "media")


def supervise(stopped: Event, backend: Path) -> None:
    children: list[subprocess.Popen[bytes]] = []
    prior_term = signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    prior_int = signal.signal(signal.SIGINT, lambda *_: stopped.set())
    try:
        for queue in QUEUES:
            children.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        str(backend / "manage.py"),
                        "runworker",
                        "--queue-group",
                        queue,
                    ],
                    cwd=backend,
                )
            )
        while not stopped.wait(0.2):
            _assert_consumers_live(children)
    finally:
        _terminate_owned(children)
        _wait_owned(children)
        signal.signal(signal.SIGTERM, prior_term)
        signal.signal(signal.SIGINT, prior_int)


def _wait_owned(children: list[subprocess.Popen[bytes]]) -> None:
    for process in children:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)


def _terminate_owned(children: list[subprocess.Popen[bytes]]) -> None:
    for process in children:
        if process.poll() is None:
            process.terminate()


def _assert_consumers_live(children: list[subprocess.Popen[bytes]]) -> None:
    if any(process.poll() is not None for process in children):
        raise RuntimeError("A reserved queue consumer stopped unexpectedly")
