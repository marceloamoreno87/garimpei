from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from hashlib import sha256
from uuid import uuid4

from django.db import connections

from garimpei.domain.robot.errors import RobotPaused
from garimpei.domain.robot.ports import RobotAdmission


def _database_call[T](callback: Callable[[], T]) -> T:
    try:
        return callback()
    finally:
        # Playwright owns an asyncio loop; ORM work uses this separate clean thread.
        # Close only that thread's connections, including failures and denied requests.
        connections.close_all()


@contextmanager
def robot_operation(robot: RobotAdmission | None, stage: str, request: str) -> Iterator[None]:
    if robot is None:
        yield
        return
    fingerprint = sha256(request.encode()).hexdigest()
    identity = fingerprint + ":" + uuid4().hex
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="robot-admission") as executor:
        permit = executor.submit(
            _database_call, lambda: robot.authorize(stage, identity, fingerprint, 0)
        ).result()
        if permit is None:
            raise RobotPaused()
        try:
            yield
        except BaseException:
            executor.submit(
                _database_call, lambda: robot.complete(permit, "unknown", "operation_interrupted")
            ).result()
            raise
        else:
            executor.submit(_database_call, lambda: robot.complete(permit)).result()
