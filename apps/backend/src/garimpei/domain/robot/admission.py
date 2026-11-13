from collections.abc import Iterator
from contextlib import contextmanager
from uuid import uuid4

from garimpei.domain.robot.errors import RobotPaused
from garimpei.domain.robot.ports import RobotAdmission


@contextmanager
def admitted_unit(
    robot: RobotAdmission | None, stage: str, key: str, revision: str = "", generation: int = 0
) -> Iterator[None]:
    if robot is None:
        yield
        return
    # Business checkpoints retain deduplication; each finite attempt gets its own receipt.
    permit = robot.authorize(stage, (key[:150] + ":" + uuid4().hex), revision, generation)
    if permit is None:
        raise RobotPaused()
    try:
        yield
    except RobotPaused:
        robot.complete(permit, "not_started", "robot_paused")
        raise
    except BaseException:
        robot.complete(permit, "unknown", "completion_unconfirmed")
        raise
    else:
        robot.complete(permit)
