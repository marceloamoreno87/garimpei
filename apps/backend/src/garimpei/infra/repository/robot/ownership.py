import os

import psutil


def process_reference() -> str:
    process = psutil.Process(os.getpid())
    return f"{process.pid}:{process.create_time()}"


def owner_is_live(reference: str) -> bool:
    fields = reference.split(":", 1)
    if len(fields) != 2 or not fields[0].isdecimal():
        return False
    try:
        process = psutil.Process(int(fields[0]))
        return (
            abs(process.create_time() - float(fields[1])) < 0.01
            and process.is_running()
            and process.status() != psutil.STATUS_ZOMBIE
        )
    except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
        return False
