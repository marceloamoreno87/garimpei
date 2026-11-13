from typing import Protocol

from garimpei.domain.robot.control import OperationOutcome, RobotCommand, RobotPermit, RobotStatus


class RobotControlRepository(Protocol):
    def command(self, value: RobotCommand) -> None: ...


class RobotQueries(Protocol):
    def status(self) -> RobotStatus: ...


class RobotAdmission(Protocol):
    def authorize(
        self, stage: str, unit_key: str, input_revision: str, resource_generation: int
    ) -> RobotPermit | None: ...

    def complete(
        self, permit: RobotPermit, outcome: OperationOutcome = "completed", reason: str = ""
    ) -> None: ...
